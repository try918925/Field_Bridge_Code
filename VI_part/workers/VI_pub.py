import zmq
import logging

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

    def send_msg(self, msg):
        try:
            self._logger.info(msg)
            self.VI2MC_pub_socket.send_string(msg)
        except Exception as error:  #如果10秒钟没有接收数据进行提示（打印 "time out"）
            self._logger.error(error)
                # print("tme out")

