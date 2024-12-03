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

        CT2MC_url = 'tcp://10.142.1.201:9002' # todo config list
        CT2MC_pub_context = zmq.Context()
        self.CT2MC_pub_socket = CT2MC_pub_context.socket(zmq.PUB)
        self.CT2MC_pub_socket.bind(CT2MC_url) 
        self.log_cnt = 0
        self.lock = threading.Lock()

    def send_msg(self, msg: str):
        with self.lock:
            try:       
                # if 'CT000' in msg or 'CT001' in msg:
                if 'CT000' in msg:
                    self.log_cnt += 1
                    if self.log_cnt > 30:
                        self.log_cnt = 0
                        self._logger.info(msg)
                else:
                    self._logger.info(msg)
                self.CT2MC_pub_socket.send_string(msg)
            except Exception as error:  
                self._logger.error(error)
    



def init_CT2MC_pub(logger:logging.Logger):
    try:
        pub = msg_pub(logger)
        print(f"Succeed to init CT2MC_pub.")
        return True, pub
    except Exception as error:
        print(f"Failed to init CT2MC_pub : '{type(error).__name__}: {error}'.")
        return False, None
    
