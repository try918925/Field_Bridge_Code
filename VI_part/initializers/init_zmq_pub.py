import zmq
import zmq
import logging
import threading
class msg_pub():
    '''
    VI -> MC: zmq pub
    '''
    def __init__(self, logger:logging.Logger):
        super().__init__()
        self._logger = logger

        VI2MC_url = 'tcp://10.142.1.202:9004' # todo config list
        VI2MC_pub_context = zmq.Context()
        self.VI2MC_pub_socket = VI2MC_pub_context.socket(zmq.PUB)
        self.VI2MC_pub_socket.bind(VI2MC_url) 
        self.log_cnt = 0
        self.VI2MC_lock = threading.Lock()

    def send_msg(self, msg: str):
        try:
            with self.VI2MC_lock:
                self.VI2MC_pub_socket.send_string(msg)
            if 'VI000' in msg or 'VI004' in msg:
                self.log_cnt += 1
                if self.log_cnt > 20:
                    self.log_cnt = 0
                    self._logger.info(msg)
                else:
                    self._logger.debug(msg)
            else:
                self._logger.info(msg)

        except Exception as error:  #如果10秒钟没有接收数据进行提示（打印 "time out"）
            self._logger.error(error)
            print(error)


def init_VI2MC_pub(logger:logging.Logger):
    try:
        pub = msg_pub(logger)
        print(f"Succeed to init VI2MC_pub.")
        return True, pub
    except Exception as error:
        print(f"Failed to init VI2MC_pub : '{type(error).__name__}: {error}'.")
        return False, None
    