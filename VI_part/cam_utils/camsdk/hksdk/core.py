import threading
# ----------------------------------------
import numpy as np
import cv2
try:
    from . import HKSDK
except ImportError:
    import HKSDK
# ----------------------------------------
# --------------------------------------------------


class Device(object):

    def __init__(self, camera_id: str,
                 host: str, port: int = 8000,
                 user: str = None, passwd: str = None,
                 resolution: tuple = (1920, 1080),
                 gpu_id: int = 0):
        # ----------------------------------------
        self._id = camera_id
        self._hostname = host
        self._port = port
        self._username = user
        self._password = passwd
        # ------------------------------
        self._user_id = -1
        self._handle_id = -1
        self._lock = threading.Lock()
        # ----------------------------------------
        ret_flag, status_code = HKSDK.init()
        if not ret_flag:
            raise OSError(f'Failed to initialize SDK -> StatusCode: {status_code}')
        # ------------------------------
        if not resolution:
            raise ValueError(f"must provide resolution.")
        self._resolution = resolution
        self._gpu_id = gpu_id

    def login(self) -> tuple:
        with self._lock:
            if self._user_id >= 0:
                return True, 0
            # ----------------------------------------
            user_id, status_code = HKSDK.login(
                self._hostname, self._username, self._password)
            if user_id >= 0:
                self._user_id = user_id
                return True, 0
            # ----------------------------------------
            return False, status_code

    def logout(self):
        with self._lock:
            if self._handle_id >= 0:
                raise ValueError(f'Failed to logout: Need close stream !')
            # ----------------------------------------
            if self._user_id < 0:
                return True, 0
            # ----------------------------------------
            ret_flag, status_code = HKSDK.logout(self._user_id)
            if ret_flag:
                self._user_id = -1
                return True, 0
            # ----------------------------------------
            return False, status_code

    def open(self):
        with self._lock:
            if self._user_id < 0:
                raise ValueError(f'Failed open stream: Need login !')
            # ----------------------------------------
            if self._handle_id >= 0:
                return True, 0
            # ----------------------------------------
            handle_id, status_code = HKSDK.open(self._user_id)
            if handle_id >= 0:
                self._handle_id = handle_id
                return True, 0
            # ----------------------------------------
            return False, status_code

    def close(self):
        with self._lock:
            if self._handle_id < 0:
                return True, 0
            # ----------------------------------------
            ret_flag, status_code = HKSDK.close(self._handle_id)
            if ret_flag:
                self._handle_id = -1
                return True, 0
            # ----------------------------------------
            return False, status_code

    def read(self, is_force=False):
        if self._handle_id < 0:
            return False, None
        # ----------------------------------------
        ret_flag, frame, width, height = HKSDK.get_frame(self._handle_id, is_force)
        if ret_flag:
            frame = frame.reshape((height+height//2, width, 1))
            frame = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_YV12)
            # ------------------------------
            if frame.shape[:2] != self._resolution[::-1]:
                frame = cv2.resize(frame, dsize=self._resolution)
            return True, frame
        # ----------------------------------------
        if is_force:
            fake_frame = np.zeros((*self._resolution[::-1], 3), dtype=np.uint8)
            return False, fake_frame
        # ----------------------------------------
        return False, None

    def read_yuv(self):
        if self._handle_id < 0:
            return False, None
        # ----------------------------------------
        ret_flag, frame, width, height = HKSDK.get_frame(self._handle_id, False)
        if ret_flag:
            return True, frame, (width, height)
        # ----------------------------------------
        return False, None, (0, 0)

    def get_ptz(self):
        with self._lock:
            if (self._user_id < 0) or (self._handle_id < 0):
                raise ValueError(f'Failed get PTZ: Need login & open stream !')
            # ----------------------------------------
            print('before get ptz')
            ret_flag, error_code, p, t, z = HKSDK.get_ptz(self._user_id, self._handle_id)
            # print(p, t, z)
            print('after get ptz')
            if not ret_flag:
                return False, error_code, (-1, -1, -1)
            # ----------------------------------------
            p = int(hex(p)[2:]) // 10
            t = int(hex(t)[2:]) // 10
            z = int(hex(z)[2:]) // 10
            return True, 0, (p, t, z)

    def set_ptz(self, p, t, z):
        p = int('0x' + str(p * 10), base=16)
        t = int('0x' + str(t * 10), base=16)
        z = int('0x' + str(z * 10), base=16)
        with self._lock:
            if (self._user_id < 0) or (self._handle_id < 0):
                raise ValueError(f'Failed set PTZ: Need login & open stream !')
            # ----------------------------------------
            ret_flag, error_code \
                = HKSDK.set_ptz(self._user_id, self._handle_id, p, t, z)
            if not ret_flag:
                return False, error_code
            # ----------------------------------------
            return True, 0

    @classmethod
    def from_uri(cls, uri):
        pass

    @property
    def host(self):
        return self._hostname

    @property
    def id(self):
        return self._id

    @property
    def is_login(self):
        with self._lock:
            return self._user_id >= 0

    @property
    def is_open(self):
        with self._lock:
            return self._handle_id >= 0



if __name__ == '__main__':
    import time
    cap = Device('66', '192.168.50.65', 8000, 'admin', 'a1234567')
    ret_flag, error_code = cap.login()
    if not ret_flag:
        print("登录失败:", error_code)
        exit()
    # time.sleep(1)
    cap.open()
    # time.sleep(1)
    # while True:
    #     ret_flag, error_code, (p, t, z) = cap.get_ptz()
    #     if ret_flag:
    #         print((p, t, z))
    #     time.sleep(1)
    while True:
        time1 = time.time()
        ret_flag, frame = cap.read()
        time2 = time.time()
        print(time2-time1)
        if ret_flag:
            cv2.imshow("frame", frame)
            cv2.waitKey(5)
        else:
            print('???')

