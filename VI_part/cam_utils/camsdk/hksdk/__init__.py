import sys
sys.path.append("./cam_utils/camsdk/hksdk")


import time
try:
    from .core import Device
except:
    from core import Device


class VideoCapture(object):

    def __init__(self, device: Device):
        self._device = device
        ret_flag, error_code = self._device.open()
        if not ret_flag:
            print('sxxx')
            return

        start_time = time.time()
        while True:
            ret_flag, frame = self._device.read()
            if not ret_flag:
                # print('a')
                if time.time() - start_time > 10:
                    # print('b')
                    self._device.close()
                    return
                time.sleep(0.001)
                continue
            break

    def isOpened(self):
        return self._device.is_open

    def read(self):
        if not self._device.is_open:
            return False, None

        start_time = time.time()
        while True:
            ret_flag, frame = self._device.read()
            if not ret_flag:
                if time.time() - start_time > 1:
                    return ret_flag, frame
                time.sleep(0.001)
                continue
            return ret_flag, frame

    def release(self):
        return self._device.close()



if __name__ == '__main__':
    import cv2

    device = Device("50.66", "192.168.50.66", 8000, "admin", "a1234567")
    device.login()
    print('is login', device.is_login)

    cap = VideoCapture(device)
    print(cap.isOpened())

    count_faild = 0
    while cap.isOpened():
        if count_faild > 10:
            print('连续多次读取失败 !')
            break

        ret_flag, frame = cap.read()
        if not ret_flag:
            count_faild += 1
            continue

        cv2.imshow("frame", frame)
        cv2.waitKey(1)

