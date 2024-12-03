from initializers import *
from global_info import *
# --------------------------------------------------
import threading
import time
import uuid
import json

class VI_heartbeat(threading.Thread):

    def __init__(self, msg_thread: threading.Thread, spreader_thread: threading.Thread):
        super().__init__()
        self.logger = error_logger
        self._VI2MC_pub = VI2MC_pub
        self._msg_thread = msg_thread
        self._spreader_thread = spreader_thread

    def run(self, ):
        time.sleep(3) # 等待5s所有线程启动
        while True:
            if not self._msg_thread.is_alive():
                error_logger.info("msg_thread is closesd")
                # todo 发送异常 
            # todo: add
            if not self._spreader_thread.is_alive():
                error_logger.info("spreader_thread is closesd")
                # todo 发送异常 

            VI000["msg_uid"] = str(uuid.uuid1())
            VI000["timestamp"] = int(time.time() * 1000)
            VI000["data"]['heartbeat'] += 1 # 1 -9999
            if VI000["data"]['heartbeat'] > 9999:
                VI000["data"]['heartbeat'] -= 9999
            if VI000["data"]['heartbeat'] % 100 == 0:
                save_global()
            set_global('VI000', VI000)
            VI2MC_pub.send_msg(json.dumps(VI000))  
            time.sleep(0.2)