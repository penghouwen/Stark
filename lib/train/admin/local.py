class EnvironmentSettings:
    def __init__(self):
        self.workspace_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr'    # Base directory for saving network checkpoints.
        self.tensorboard_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/tensorboard'    # Directory for tensorboard files.
        self.pretrained_networks = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/pretrained_networks'
        self.lasot_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/lasot'
        self.got10k_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/got10k/train'
        self.lasot_lmdb_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/lasot_lmdb'
        self.got10k_lmdb_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/got10k_lmdb'
        self.trackingnet_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/trackingnet'
        self.trackingnet_lmdb_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/trackingnet_lmdb'
        self.coco_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/coco'
        self.coco_lmdb_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/coco_lmdb'
        self.lvis_dir = ''
        self.sbd_dir = ''
        self.imagenet_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/vid'
        self.imagenet_lmdb_dir = '/media/ln/81080cea-dc9b-4612-901b-66970e8706d4/ln/siamtr/data/vid_lmdb'
        self.imagenetdet_dir = ''
        self.ecssd_dir = ''
        self.hkuis_dir = ''
        self.msra10k_dir = ''
        self.davis_dir = ''
        self.youtubevos_dir = ''
