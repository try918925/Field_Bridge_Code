from pathlib import Path
import sys
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # 本机目录
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH


from cmd_utils import *
from PID_ctrl import *
from model import *