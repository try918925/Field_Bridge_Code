import os
LOG_DIR = "./log"
RESULT_DIR = "./log/guid_result"
if not os.path.exists(RESULT_DIR):
    os.makedirs(RESULT_DIR)
DEBUG = True
# --------------------------------------------------
YOLO_DEVICE = "cuda:1"
YOLO_CLASSES = ['car', 'car_front', 'target', '20_container', '40_container',
                'car_board', 'center', 'biaoba', 'lock', 'hanger']  # notice to be int ['door', 'nodoor']
# ----------------------------------------
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
YOLO_NET_CONF = os.path.join(CURRENT_DIR, 'yolov5s.yaml')
YOLO_WEIGHT_PATH = './weights/plate_hanger.pt'
YOLO_INFER_SIZE = (640, 640)
YOLO_PADDING_COLOR = (114, 114, 114)
YOLO_THRESHOLD_CONF = 0.1    # 置信度的过滤值
YOLO_THRESHOLD_IOU = 0.2
YOLO_INFER_HALF = True # use FP16 half-precision inference
YOLO_INFER_DNN = False # use OpenCV DNN for ONNX inference

