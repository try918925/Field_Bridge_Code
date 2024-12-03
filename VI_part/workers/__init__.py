from pathlib import Path
import sys

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # 本机目录
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH

from heartbeat import VI_heartbeat
from recv_plc import recv_plc
from process_MC2VI import process_MC2VI
from spreader_pos import spreader_pos
from land_beam import cemian_ocr
from guid_new import det_guid
from area_monitor import gantry_monitor, trolley_monitor
from joinbeam_cntr import left_joinbeam, right_joinbeam
from car_num import car_num
from fog_det import FogDetect
from press_plate_det import press_plate
from debug_server import debug_server
from truck_head import car_head_detect
