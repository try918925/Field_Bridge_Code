LOG_DIR = "./log"
RESULT_DIR = "./result"

# --------------------------------------------------
YOLO_DEVICE = "cuda:0"
YOLO_WEIGHT_PATH = 'best.engine'
YOLO_CLASSES = ['door', 'nodoor']
YOLO_INFER_SIZE = (224, 224)
YOLO_INFER_HALF = True # use FP16 half-precision inference
YOLO_INFER_DNN = False # use OpenCV DNN for ONNX inference