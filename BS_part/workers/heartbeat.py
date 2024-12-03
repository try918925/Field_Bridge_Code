from initializers import *
from global_info import *
# --------------------------------------------------
import threading
import time
import uuid
import json

class BS_heartbeat(threading.Thread):

    def __init__(self, MCPUB_msg_thread: threading.Thread, MC2BS_msg_thread: threading.Thread, ):
        super().__init__()
        self.logger = error_logger
        self._BS2MC_pub = BS2MC_pub
        self._MCPUB_msg_thread = MCPUB_msg_thread
        self._MC2BS_msg_thread = MC2BS_msg_thread
        
    def run(self, ):
        time.sleep(3) # 等待5s所有线程启动
        while True:
            time.sleep(0.2)
            if not self._MCPUB_msg_thread.is_alive():
                error_logger.info("_MCPUB_msg_thread is closesd")
                # todo 发送异常 
                continue
            if not self._MC2BS_msg_thread.is_alive():
                error_logger.info("_MC2BS_msg_thread is closesd")
                # todo 发送异常
                continue

            BS000 = get_global('BS000')
            BS000["msg_uid"] = str(uuid.uuid1())
            BS000["timestamp"] = int(time.time() * 1000)
            BS000["data"]['heartbeat'] += 1 # 1 -9999
            if BS000["data"]['heartbeat'] > 9999:
                BS000["data"]['heartbeat'] -= 9999
            if BS000["data"]['heartbeat'] % 100 == 0:
                save_global()
            set_global('BS000', BS000)
            BS2MC_pub.send_msg(json.dumps(BS000))  
            