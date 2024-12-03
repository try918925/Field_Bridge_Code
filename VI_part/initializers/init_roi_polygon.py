import numpy as np
import cv2
from shapely.geometry import Polygon
# --------------------------------------------------


class RoiPolygon(object):

    def __init__(self, polygon_points_list):
        self.polygon_points = polygon_points_list
        self._polygon_points_array = np.array(polygon_points_list, dtype=np.int32)
        self._polygon = Polygon(self._polygon_points_array)
        self._convex_hull = self._polygon.convex_hull

    def is_intersects_by_p1p2(self, p1p2):
        x1, y1, x2, y2 = p1p2
        obj_polygon_points_array \
            = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
        obj_polygon = Polygon(obj_polygon_points_array)
        obj_convex_hull = obj_polygon.convex_hull
        # ----------------------------------------
        return self._convex_hull.intersects(obj_convex_hull)
    
    def show_polygon(self, img, warning_level):
        color_list = [[0, 0, 255], [255, 0, 0]]
        cv2.polylines(img, [self.polygon_points], isClosed= True, color= color_list[warning_level], thickness= 3)
        return img


def init_roi_polygon(roi_polygon_points):
    try:
        roi_polygon = RoiPolygon(roi_polygon_points)
        # print("Succeed to init roi polygon obj.")
        return True, roi_polygon
    
    except Exception as error:
        print(f"Failed to init roi polygon: '{type(error).__name__}: {error}'.")
        return False, None