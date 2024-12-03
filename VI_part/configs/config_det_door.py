import os
LOG_DIR = "./log"
RESULT_DIR = "./log/door_result"
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)
# --------------------------------------------------
YOLO_DEVICE = "cuda:1"

YOLO_CLASSES = ['BD', 'LH', 'RH', 'LL', 'RL','FD'] # notice to be int ['door', 'nodoor']

# ----------------------------------------
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
YOLO_NET_CONF = os.path.join(CURRENT_DIR, 'yolov5s.yaml')
YOLO_WEIGHT_PATH = './weights/door.pt'
YOLO_INFER_SIZE = (640, 640)
YOLO_PADDING_COLOR = (114, 114, 114)
YOLO_THRESHOLD_CONF = 0.35             # 置信度的过滤值
YOLO_THRESHOLD_IOU = 0.5
YOLO_INFER_HALF = True # use FP16 half-precision inference
YOLO_INFER_DNN = False # use OpenCV DNN for ONNX inference

