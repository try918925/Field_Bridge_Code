from pathlib import Path
import sys
import os

os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from workers import *
from configs import config_det_guid


def main():
    refresh_MC001 = recv_plc()
    spread_pos_thread = spreader_pos()
    heartbeat = VI_heartbeat(refresh_MC001, spread_pos_thread)
    left_joinbeam_thread = left_joinbeam()
    right_joinbeam_thread = right_joinbeam()
    car_num_thread = car_num()
    #
    land_cemian_ocr = cemian_ocr()
    guid_119_thread = det_guid(config_det_guid)
    # trolley_monitor_thread = trolley_monitor()
    gantry_monitor_thread = gantry_monitor()
    fog_det_thread = FogDetect()
    debug_server_thread = debug_server()
    truck_head_detect = car_head_detect()
    # press_plate_thread = press_plate()

    process_MC2VI_thread = process_MC2VI()
    process_MC2VI_thread.start()

    refresh_MC001.start()
    spread_pos_thread.start()
    heartbeat.start()
    left_joinbeam_thread.start()
    right_joinbeam_thread.start()
    car_num_thread.start()
    land_cemian_ocr.start()
    guid_119_thread.start()

    debug_server_thread.start()
    truck_head_detect.start()

    # press_plate_thread.start()
    # trolley_monitor_thread.start()
    gantry_monitor_thread.start()
    fog_det_thread.start()


if __name__ == '__main__':
    main()
