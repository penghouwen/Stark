from lib.models.stark.backbone import build_backbone
from lib.models.stark.head import build_box_head
from lib.models.stark.stark_s import STARKS
from lib.models.stark.transformer import build_transformer


class SiamTr(STARKS):
    def __init__(self, backbone, transformer, box_head, num_queries,
                 aux_loss=False, head_type="PROB_BOX"):
        super().__init__(
            backbone,
            transformer,
            box_head,
            num_queries,
            aux_loss,
            head_type
        )

    def forward_box_head(self, hs, memory):
        """
        hs: output embeddings (1, B, N, C)
        memory: encoder embeddings (HW1+HW2, B, C)"""
        if self.head_type == "PROB_BOX":
            self.box_head(hs)
        else:
            super().forward_box_head(hs, memory)


def build_siam_tr(cfg):
    backbone = build_backbone(cfg)  # backbone and positional encoding are built together
    transformer = build_transformer(cfg)
    box_head = build_box_head(cfg)
    model = SiamTr(
        backbone,
        transformer,
        box_head,
        num_queries=cfg.MODEL.NUM_OBJECT_QUERIES,
        aux_loss=cfg.TRAIN.DEEP_SUPERVISION,
        head_type=cfg.MODEL.HEAD_TYPE
    )
    return model
