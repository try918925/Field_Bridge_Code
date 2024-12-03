from pathlib import Path
import sys
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # 本机目录
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH

from heartbeat import BS_heartbeat
from recv_plc import recv_plc
from recv_MC2BS import recv_MC2BS