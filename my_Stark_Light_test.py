import os
import sys
import argparse
import cv2
from easydict import EasyDict as edict
from PIL import Image
import yaml
import numpy as np
from collections import OrderedDict
import onnxruntime
import time
import math

prj_dir = r'C:\Users\zadorozhnyy.v\Downloads\mystark'
save_dir = r'C:\Users\zadorozhnyy.v\Downloads\mystark'    
data_dir = r'C:\Users\zadorozhnyy.v\Downloads\Stark-main\data\got10k\test'

def process(img_arr: np.ndarray, amask_arr: np.ndarray):
    mean = np.array([0.485, 0.456, 0.406]).reshape((1, 3, 1, 1))
    std = np.array([0.229, 0.224, 0.225]).reshape((1, 3, 1, 1))
    """img_arr: (H,W,3), amask_arr: (H,W)"""
    # Deal with the image patch
    img_arr_4d = img_arr[np.newaxis, :, :, :].transpose(0, 3, 1, 2)
    img_arr_4d = (img_arr_4d / 255.0 - mean) / std  # (1, 3, H, W)
    # Deal with the attention mask
    amask_arr_3d = amask_arr[np.newaxis, :, :]  # (1,H,W)
    return img_arr_4d.astype(np.float32), amask_arr_3d.astype(np.bool)

def sample_target(im, target_bb, search_area_factor, output_sz=None, mask=None):
    """ Extracts a square crop centered at target_bb box, of area search_area_factor^2 times target_bb area

    args:
        im - cv image
        target_bb - target box [x, y, w, h]
        search_area_factor - Ratio of crop size to target size
        output_sz - (float) Size to which the extracted crop is resized (always square). If None, no resizing is done.

    returns:
        cv image - extracted crop
        float - the factor by which the crop has been resized to make the crop size equal output_size
    """
    if not isinstance(target_bb, list):
        x, y, w, h = target_bb.tolist()
    else:
        x, y, w, h = target_bb
    # Crop image
    crop_sz = math.ceil(math.sqrt(w * h) * search_area_factor)

    if crop_sz < 1:
        raise Exception('Too small bounding box.')

    x1 = round(x + 0.5 * w - crop_sz * 0.5)
    x2 = x1 + crop_sz

    y1 = round(y + 0.5 * h - crop_sz * 0.5)
    y2 = y1 + crop_sz

    x1_pad = max(0, -x1)
    x2_pad = max(x2 - im.shape[1] + 1, 0)

    y1_pad = max(0, -y1)
    y2_pad = max(y2 - im.shape[0] + 1, 0)

    # Crop target
    im_crop = im[y1 + y1_pad:y2 - y2_pad, x1 + x1_pad:x2 - x2_pad, :]
    if mask is not None:
        mask_crop = mask[y1 + y1_pad:y2 - y2_pad, x1 + x1_pad:x2 - x2_pad]

    # Pad
    im_crop_padded = cv2.copyMakeBorder(im_crop, y1_pad, y2_pad, x1_pad, x2_pad, cv2.BORDER_CONSTANT)
    # deal with attention mask
    H, W, _ = im_crop_padded.shape
    att_mask = np.ones((H,W))
    end_x, end_y = -x2_pad, -y2_pad
    if y2_pad == 0:
        end_y = None
    if x2_pad == 0:
        end_x = None
    att_mask[y1_pad:end_y, x1_pad:end_x] = 0
    if mask is not None:
        mask_crop_padded = F.pad(mask_crop, pad=(x1_pad, x2_pad, y1_pad, y2_pad), mode='constant', value=0)

    if output_sz is not None:
        resize_factor = output_sz / crop_sz
        im_crop_padded = cv2.resize(im_crop_padded, (output_sz, output_sz))
        att_mask = cv2.resize(att_mask, (output_sz, output_sz)).astype(np.bool_)
        if mask is None:
            return im_crop_padded, resize_factor, att_mask
        mask_crop_padded = \
        F.interpolate(mask_crop_padded[None, None], (output_sz, output_sz), mode='bilinear', align_corners=False)[0, 0]
        return im_crop_padded, resize_factor, att_mask, mask_crop_padded

    else:
        if mask is None:
            return im_crop_padded, att_mask.astype(np.bool_), 1.0
        return im_crop_padded, 1.0, att_mask.astype(np.bool_), mask_crop_padded  

def clip_box(box: list, H, W, margin=0):
    x1, y1, w, h = box
    x2, y2 = x1 + w, y1 + h
    x1 = min(max(0, x1), W-margin)
    x2 = min(max(margin, x2), W)
    y1 = min(max(0, y1), H-margin)
    y2 = min(max(margin, y2), H)
    w = max(margin, x2-x1)
    h = max(margin, y2-y1)
    return [x1, y1, w, h] 

def map_box_back(state, pred_box: list, search_size, resize_factor: float):
    cx_prev, cy_prev = state[0] + 0.5 * state[2], state[1] + 0.5 * state[3]
    cx, cy, w, h = pred_box
    half_side = 0.5 * search_size / resize_factor
    cx_real = cx + (cx_prev - half_side)
    cy_real = cy + (cy_prev - half_side)
    return [cx_real - 0.5 * w, cy_real - 0.5 * h, w, h]

def save_res(seq_num, data):
    seq_name = open(os.path.join(data_dir, "list.txt"), "r").readlines()[seq_num]
    file = os.path.join(prj_dir,"lib\\test\\tracking_results\\stark_lightning_X_trt\\baseline_rephead_4_lite_search5\\got10k", seq_name.split('\n')[0] + ".txt")
    tracked_bb = np.array(data).astype(int)
    np.savetxt(file, tracked_bb, delimiter='\t', fmt='%d')    

def get_new_frame(frame_id, seq_num):
    seq_name = open(os.path.join(data_dir, "list.txt"), "r").readlines()[seq_num]
    imgs = [img for img in os.listdir(os.path.join(data_dir, seq_name.split('\n')[0])) if img.endswith(".jpg")]
    if len(imgs) <= frame_id:
        return None
    im = cv2.imread(os.path.join(data_dir, seq_name.split('\n')[0], imgs[frame_id]))
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)

def get_init_box(seq_num):
    seq_name = open(os.path.join(data_dir, "list.txt"), "r").readlines()[seq_num]
    path = os.path.join(data_dir, seq_name.split('\n')[0], "groundtruth.txt")
    ground_truth_rect = np.loadtxt(path, delimiter=',', dtype=np.float64)
    return ground_truth_rect

class TrackerParams:
    """Class for tracker parameters."""
    def set_default_values(self, default_vals: dict):
        for name, val in default_vals.items():
            if not hasattr(self, name):
                setattr(self, name, val)

    def get(self, name: str, *default):
        """Get a parameter value with the given name. If it does not exists, it return the default value given as a
        second argument or returns an error if no default value is given."""
        if len(default) > 1:
            raise ValueError('Can only give one default value.')

        if not default:
            return getattr(self, name)

        return getattr(self, name, default[0])

    def has(self, name: str):
        """Check if there exist a parameter with the given name."""
        return hasattr(self, name)

def my_tracker(get_new_frame, get_init_box, seq_num):
    def _edict2dict(dest_dict, src_edict):
            if isinstance(dest_dict, dict) and isinstance(src_edict, dict):
                for k, v in src_edict.items():
                    if not isinstance(v, edict):
                        dest_dict[k] = v
                    else:
                        dest_dict[k] = {}
                        _edict2dict(dest_dict[k], v)
            else:
                return

    def gen_config(config_file):
        cfg_dict = {}
        _edict2dict(cfg_dict, cfg)
        with open(config_file, 'w') as f:
            yaml.dump(cfg_dict, f, default_flow_style=False)


    def _update_config(base_cfg, exp_cfg):
        if isinstance(base_cfg, dict) and isinstance(exp_cfg, edict):
            for k, v in exp_cfg.items():
                if k in base_cfg:
                    if not isinstance(v, dict):
                        base_cfg[k] = v
                    else:
                        _update_config(base_cfg[k], v)
                else:
                    raise ValueError("{} not exist in config.py".format(k))
        else:
            return

    def update_config_from_file(filename):
        exp_config = None
        with open(filename) as f:
            exp_config = edict(yaml.safe_load(f))
            _update_config(cfg, exp_config)

    """Get parameters."""
    params = TrackerParams()
    cfg = edict()

    # MODEL
    cfg.MODEL = edict()
    cfg.MODEL.HEAD_TYPE = "CORNER_LITE"
    cfg.MODEL.HIDDEN_DIM = 256
    cfg.MODEL.HEAD_DIM = 256  # channel in the corner head
    # MODEL.BACKBONE
    cfg.MODEL.BACKBONE = edict()
    cfg.MODEL.BACKBONE.TYPE = "RepVGG-A0"  # resnet50, resnext101_32x8d
    cfg.MODEL.BACKBONE.OUTPUT_LAYERS = ["stage3"]
    cfg.MODEL.BACKBONE.DILATION = False
    cfg.MODEL.BACKBONE.LAST_STAGE_BLOCK = 14
    # MODEL.TRANSFORMER
    cfg.MODEL.TRANSFORMER = edict()
    cfg.MODEL.TRANSFORMER.NHEADS = 8
    cfg.MODEL.TRANSFORMER.DROPOUT = 0.1
    cfg.MODEL.TRANSFORMER.DIM_FEEDFORWARD = 2048

    # TRAIN
    cfg.TRAIN = edict()
    cfg.TRAIN.DISTILL = False
    cfg.TRAIN.DISTILL_LOSS_TYPE = "KL"
    cfg.TRAIN.AMP = False
    cfg.TRAIN.LR = 0.0001
    cfg.TRAIN.WEIGHT_DECAY = 0.0001
    cfg.TRAIN.EPOCH = 500
    cfg.TRAIN.LR_DROP_EPOCH = 400
    cfg.TRAIN.BATCH_SIZE = 16
    cfg.TRAIN.NUM_WORKER = 8
    cfg.TRAIN.OPTIMIZER = "ADAMW"
    cfg.TRAIN.BACKBONE_MULTIPLIER = 0.1
    cfg.TRAIN.GIOU_WEIGHT = 2.0
    cfg.TRAIN.L1_WEIGHT = 5.0
    cfg.TRAIN.DEEP_SUPERVISION = False
    cfg.TRAIN.FREEZE_BACKBONE_BN = True
    cfg.TRAIN.BACKBONE_TRAINED_LAYERS = ['stage2', 'stage3']
    cfg.TRAIN.PRINT_INTERVAL = 50
    cfg.TRAIN.VAL_EPOCH_INTERVAL = 20
    cfg.TRAIN.GRAD_CLIP_NORM = 0.1
    # TRAIN.SCHEDULER
    cfg.TRAIN.SCHEDULER = edict()
    cfg.TRAIN.SCHEDULER.TYPE = "step"
    cfg.TRAIN.SCHEDULER.DECAY_RATE = 0.1

    # DATA
    cfg.DATA = edict()
    cfg.DATA.MEAN = [0.485, 0.456, 0.406]
    cfg.DATA.STD = [0.229, 0.224, 0.225]
    cfg.DATA.MAX_SAMPLE_INTERVAL = 200
    # DATA.TRAIN
    cfg.DATA.TRAIN = edict()
    cfg.DATA.TRAIN.DATASETS_NAME = ["LASOT", "GOT10K_vottrain"]
    cfg.DATA.TRAIN.DATASETS_RATIO = [1, 1]
    cfg.DATA.TRAIN.SAMPLE_PER_EPOCH = 60000
    # DATA.VAL
    cfg.DATA.VAL = edict()
    cfg.DATA.VAL.DATASETS_NAME = ["GOT10K_votval"]
    cfg.DATA.VAL.DATASETS_RATIO = [1]
    cfg.DATA.VAL.SAMPLE_PER_EPOCH = 10000
    # DATA.SEARCH
    cfg.DATA.SEARCH = edict()
    cfg.DATA.SEARCH.SIZE = 320
    cfg.DATA.SEARCH.FEAT_SIZE = 20
    cfg.DATA.SEARCH.FACTOR = 5.0
    cfg.DATA.SEARCH.CENTER_JITTER = 4.5
    cfg.DATA.SEARCH.SCALE_JITTER = 0.5
    # DATA.TEMPLATE
    cfg.DATA.TEMPLATE = edict()
    cfg.DATA.TEMPLATE.SIZE = 128
    cfg.DATA.TEMPLATE.FEAT_SIZE = 8
    cfg.DATA.TEMPLATE.FACTOR = 2.0
    cfg.DATA.TEMPLATE.CENTER_JITTER = 0
    cfg.DATA.TEMPLATE.SCALE_JITTER = 0

    # TEST
    cfg.TEST = edict()
    cfg.TEST.TEMPLATE_FACTOR = 2.0
    cfg.TEST.TEMPLATE_SIZE = 128
    cfg.TEST.SEARCH_FACTOR = 5.0
    cfg.TEST.SEARCH_SIZE = 320
    cfg.TEST.EPOCH = 500
    yaml_name = "baseline_rephead_4_lite_search5"
    
    # update default config from yaml file
    yaml_file = os.path.join(prj_dir, 'experiments/stark_lightning_X_trt/%s.yaml' % yaml_name)

    update_config_from_file(yaml_file)
    params.cfg = cfg
    print("test config: ", cfg)

    # template and search region
    params.template_factor = cfg.TEST.TEMPLATE_FACTOR
    params.template_size = cfg.TEST.TEMPLATE_SIZE
    params.search_factor = cfg.TEST.SEARCH_FACTOR
    params.search_size = cfg.TEST.SEARCH_SIZE

    # Network checkpoint path
    params.checkpoint = os.path.join(save_dir,
                                     "checkpoints/train/stark_lightning_X_trt/%s/STARKLightningXtrt_ep%04d.pth.tar" %
                                     (yaml_name, cfg.TEST.EPOCH))
    # whether to save boxes from all queries
    params.save_all_boxes = False
    
    gpu_id = 0
    providers = ["CUDAExecutionProvider"]
    provider_options = [{"device_id": str(gpu_id)}]
    ort_sess_z = onnxruntime.InferenceSession("backbone_bottleneck_pe.onnx", providers=providers,
                                                   provider_options=provider_options)
    ort_sess_x = onnxruntime.InferenceSession("complete.onnx", providers=providers,
                                                   provider_options=provider_options)
    frame_id = 0
    ort_outs_z = []

    state = get_init_box(seq_num)
    image = get_new_frame(frame_id, seq_num) 
    z_patch_arr, _, z_amask_arr = sample_target(image, state, params.template_factor, output_sz=params.template_size)
    #print(z_patch_arr)
    template, template_mask = process(z_patch_arr, z_amask_arr)
    # forward the template once
    ort_inputs = {'img_z': template, 'mask_z': template_mask}
    ort_outs_z = ort_sess_z.run(None, ort_inputs)
    outputs = []
    outputs.append(state)
    frame_id = 1
    image = get_new_frame(frame_id, seq_num) 
    while image is not None:
        H, W, _ = image.shape
        
        x_patch_arr, resize_factor, x_amask_arr = sample_target(image, state, params.search_factor,
                                                                output_sz=params.search_size)  # (x1, y1, w, h)
        search, search_mask = process(x_patch_arr, x_amask_arr)

        ort_inputs = {'img_x': search,
                      'mask_x': search_mask,
                      'feat_vec_z': ort_outs_z[0],
                      'mask_vec_z': ort_outs_z[1],
                      'pos_vec_z': ort_outs_z[2],
                      }

        ort_outs = ort_sess_x.run(None, ort_inputs)
        if frame_id == 1:
            print(ort_outs[0].reshape(4))
        pred_box = (ort_outs[0].reshape(4) * params.search_size / resize_factor).tolist()  # (cx, cy, w, h) [0,1]
        # get the final box result
        state = clip_box(map_box_back(state, pred_box, params.search_size, resize_factor), H, W, margin=10)

        outputs.append(state)
        frame_id += 1
        image = get_new_frame(frame_id, seq_num) 

    return outputs
def main():
    parser = argparse.ArgumentParser(description='Run tracker on sequence or dataset.')
    parser.add_argument('--sequence', type=str, default=None, help='Sequence number')
    args = parser.parse_args()
    seq_num = int(args.sequence)
    outputs = my_tracker(get_new_frame, get_init_box, seq_num)
    save_res(seq_num, outputs)
if __name__ == '__main__':
    main()