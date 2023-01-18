# 比如要裁剪第一个字符:
from cnocr import CnOcr

ocr = CnOcr(rec_model_name='densenet_lite_136-fc', det_model_name='naive_det', cand_alphabet='0123456789')
out = ocr.ocr("screen.bmp")
print(out)
