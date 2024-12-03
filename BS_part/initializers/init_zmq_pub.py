import zmq
import zmq
import logging

class msg_pub():
    '''
    VI -> MC: zmq pub
    '''
    def __init__(self, logger:logging.Logger):
        super().__init__()
        self._logger = logger

        # BS2MC_url = 'tcp://127.0.0.1:9008' # todo config list
        BS2MC_url = 'tcp://10.142.1.202:9008' # todo config list
        BS2MC_pub_context = zmq.Context()
        self.BS2MC_pub_socket = BS2MC_pub_context.socket(zmq.PUB)
        self.BS2MC_pub_socket.bind(BS2MC_url) 
        self.log_cnt = 0

    def send_msg(self, msg: str):
        try:       
            if 'BS000' in msg:
                self.log_cnt += 1
                if self.log_cnt > 20:
                    self.log_cnt = 0
                    self._logger.info(msg)
                else:
                    self._logger.debug(msg)
            else:
                self._logger.info(msg)
            self.BS2MC_pub_socket.send_string(msg)
        except Exception as error:  #如果10秒钟没有接收数据进行提示（打印 "time out"）
            self._logger.error(error)
                # print("tme out")


def init_BS2MC_pub(logger:logging.Logger):
    try:
        pub = msg_pub(logger)
        print(f"Succeed to init BS2MC_pub.")
        return True, pub
    except Exception as error:
        print(f"Failed to init BS2MC_pub : '{type(error).__name__}: {error}'.")
        return False, None
    