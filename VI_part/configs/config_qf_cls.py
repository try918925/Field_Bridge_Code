import os
LOG_DIR = "./log"
RESULT_DIR = "./log/result_fog"
# --------------------------------------------------
YOLO_DEVICE = "cuda:0"
YOLO_CLASSES = ['0', '1']
# ----------------------------------------
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
YOLO_WEIGHT_PATH = './weights/qf_cls.pt'
YOLO_INFER_SIZE = (224, 224)
YOLO_INFER_HALF = True # use FP16 half-precision inference
YOLO_INFER_DNN = False # use OpenCV DNN for ONNX inference

