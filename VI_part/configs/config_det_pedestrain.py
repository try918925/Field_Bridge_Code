LOG_DIR = "./log"
RESULT_DIR = "./log/result_pedestrain"
import os
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)
# --------------------------------------------------
YOLO_DEVICE = "cuda:0"

YOLO_CLASSES = ['pedestrian'] # notice to be int ['door', 'nodoor']

# ----------------------------------------
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
YOLO_NET_CONF = os.path.join(CURRENT_DIR, 'yolov5s.yaml')
YOLO_WEIGHT_PATH = './weights/pedestrian_det.pt'
YOLO_INFER_SIZE = (640, 640)
YOLO_PADDING_COLOR = (114, 114, 114)
YOLO_THRESHOLD_CONF = 0.99       # 置信度的过滤值
YOLO_THRESHOLD_IOU = 0.45
YOLO_INFER_HALF = True # use FP16 half-precision inference
YOLO_INFER_DNN = False # use OpenCV DNN for ONNX inference

