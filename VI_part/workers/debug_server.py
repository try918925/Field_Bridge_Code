'''
    开启端口, 并发送给主控
'''
import threading
import socket
import time
import uuid
import json

from initializers import *
from global_info import *



class debug_server(threading.Thread):
    def __init__(self, ):
        super().__init__()
 

    def run(self, ):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = ("127.0.0.1", 10001)
        server_socket.bind(address)  # 为服务器绑定一个固定的地址，ip和端口
        server_socket.settimeout(1000)  #设置一个时间提示，如果10秒钟没接到数据进行提示
        received_msg = ""   

        while True:
            try:
                receive_data, client = server_socket.recvfrom(1024)
                received_msg = receive_data.decode()
                VI2MC_pub.send_msg(received_msg)
            except socket.timeout:  
                pass

def test_VI003():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ("127.0.0.1", 10001)     

    while True:
        for i in range(100):
            time.sleep(1)
            Ep = {
                "exception_code": 'E209',  # int,异常代码
                "detail": "",  # string,具体信息描述
                "happen_time": str(int(time.time() * 1000)),  # long, 时间戳,单位毫秒
                "has_solved": False,  # bool,是否已解决
                "solve_time": None  # long, 时间戳,单位毫秒
            }
            VI003 = {
                "msg_uid": str(uuid.uuid1()),  # string,消息序号
                "msg_name": "VI003",  # string,消息名称
                "sender": "VI",  # string,发送方
                "timestamp": int(time.time() * 1000),  # long, 时间戳,单位毫秒
                "receiver": "MC",  # string,接收方
                "craneId": "404-1",  # string, 设备号
                "data": Ep  # Exception,异常信息
            }
            send_msg = json.dumps(VI003, ensure_ascii=False)
            client_socket.sendto(send_msg.encode(), server_address)
        