from pathlib import Path
import sys
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # 本机目录
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH

from init_logger import init_logger
from init_zmq_pub import init_BS2MC_pub

# 创建日志模块
import logging
ret, main_logger = init_logger(name="main_msg", level= logging.INFO, log_file='./log/main_msg.log')
ret, key_logger = init_logger(name="key_msg", level= logging.INFO, log_file='./log/key_msg.log')
ret, error_logger = init_logger(name="error_msg", level= logging.INFO, log_file='./log/error_msg.log')

# 创建消息转发模块
ret, BS2MC_pub = init_BS2MC_pub(main_logger)

