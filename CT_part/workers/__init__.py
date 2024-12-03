from pathlib import Path
import sys
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # 本机目录
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH

from heartbeat import CT_heartbeat
from recv_plc import recv_plc
from recv_MC2CT import recv_MC2CT
from safe_ctrl import ctrl_monitor
from relative_pos import cal_relative_pos
from nowtime_lock import cal_midlock
from anti_swing import thread_anti_swing