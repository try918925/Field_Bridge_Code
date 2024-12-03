import cv2
import logging
from cam_utils.camsdk import hksdk as camera_sdk

def init_camera(camera_info, logger:logging.Logger, vedio_cam=False):
    '''
    初始化相机, 反馈ret - device
    camera_info = {camera_id: str,  host: str, port: int = 8000,
                 user: str = None, passwd: str = None,
                 resolution: tuple = (1920, 1080), gpu_id: int = 0}
    logger: logging.Logger 
    vedio_cam: True->vedio or cam, default to False
    '''
    if vedio_cam:
        try:
            cam_device = cv2.VideoCapture(camera_info["ip"])
            logger.debug("Success to init camera:\n{}.".format(camera_info))
            return True, cam_device
        except Exception as error:
            logger.debug(f"Failed to init camera\n{camera_info}:\n '{type(error).__name__}: {error}'")
            return False, None       

    else:    
        try:
            device = camera_sdk.Device(
                    camera_id=camera_info["comment"],
                    host=camera_info["ip"],
                    port=8000,
                    user=camera_info["username"],
                    passwd=camera_info["password"],
                    resolution=camera_info["resolution"],
                    gpu_id=camera_info["gpu_id"]
                )
            
            ret_flag, error_code = device.login()
            if not ret_flag:
                logger.debug(f"Failed to login camera - {device.id} ({device.host}): '{error_code}'")
                return False, None
            ret_flag, error_code = device.open()
            if not ret_flag:
                logger.debug(f"Failed to open camera - {device.id} ({device.host}): '{error_code}'")
                return False, None
            # ------------------------------
            logger.info(f"Success to init cameras - {device.id} ({device.host}):")
            return True, device
        # ----------------------------------------
        except Exception as error:
            logger.error(f"Failed to init cameras: '{type(error).__name__}: {error}'")
            return False, None