import threading
# ----------------------------------------
import numpy as np
import cv2
try:
    from . import DP
except ImportError:
    import DP
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
        self._uri = f"rtsp://{self._username}:{self._password}@{self._hostname}:554/Streaming/Channels/101"
        self._user_id = -1
        self._lock = threading.Lock()
        # ------------------------------
        ret_flag, status_code = DP.init()
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
            status_code, user_id = DP.login()
            if user_id >= 0:
                self._user_id = user_id
                return True, 0
            # ----------------------------------------
            return False, status_code

    def logout(self):
        with self._lock:
            if self._user_id < 0:
                return True, 0
            # ----------------------------------------
            ret_flag, status_code = DP.logout(self._user_id)
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
            ret_flag, status_code = DP.open(self._uri, self._user_id,
                                            self._resolution[0], self._resolution[1],
                                            self._gpu_id)
            if ret_flag:
                return True, 0
            # ----------------------------------------
            return False, status_code

    def close(self):
        with self._lock:
            if self._user_id < 0:
                return True, 0
            # ----------------------------------------
            ret_flag, status_code = DP.close(self._user_id)
            if ret_flag:
                return True, 0
            # ----------------------------------------
            return False, status_code

    def read(self, is_force=False):
        if self._user_id < 0:
            return False, None
        # ----------------------------------------
        ret_flag, frame, width, height = DP.get_frame(self._user_id, is_force)
        if ret_flag:
            frame = frame.reshape(height, width, 3)
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
            return self._user_id >= 0
