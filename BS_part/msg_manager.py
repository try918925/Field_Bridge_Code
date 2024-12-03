from pathlib import Path
import sys
import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative


from global_info import *
from initializers import *
from workers import *

import logging
import socket
import threading
import time
import zmq

def main():
    refresh_MC001 = recv_plc()
    process_MC2BS = recv_MC2BS()
    heartbeat = BS_heartbeat(refresh_MC001, process_MC2BS)

    refresh_MC001.start()
    process_MC2BS.start()
    heartbeat.start()

    
if __name__ == '__main__':
    main()
