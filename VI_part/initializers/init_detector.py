# from algorithms.yolox import YOLOXDetector
from algorithms.yolov5.predictor.det_predictor import YOLOv5Detector


def init_detector(yolox_config):
    try:
        detector = YOLOv5Detector.from_config(yolox_config)
        print("Succeed to init pedestrian detector.")
        return True, detector
    
    except Exception as error:
        print(f"Failed to init pedestrian detector: '{type(error).__name__}: {error}'.")
        return False, None
