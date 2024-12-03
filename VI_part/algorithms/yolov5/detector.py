import colorsys
import pickle
# ----------------------------------------
import numpy
import cv2
import torch
from pathlib import Path
import sys
import os
# ----------------------------------------
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from ultralytics.utils.plotting import Annotator, colors, save_one_box

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from utils.torch_utils import select_device, smart_inference_mode
from .models.yolo import Model
# --------------------------------------------------

def scale_coords(img1_shape, coords, img0_shape, ratio_pad=None):
    # Rescale coords (xyxy) from img1_shape to img0_shape
    if ratio_pad is None:  # calculate from img0_shape
        gain = min(img1_shape[0] / img0_shape[0], img1_shape[1] / img0_shape[1])  # gain  = old / new
        pad = (img1_shape[1] - img0_shape[1] * gain) / 2, (img1_shape[0] - img0_shape[0] * gain) / 2  # wh padding
    else:
        gain = ratio_pad[0][0]
        pad = ratio_pad[1]

    coords[:, [0, 2]] -= pad[0]  # x padding
    coords[:, [1, 3]] -= pad[1]  # y padding
    coords[:, :4] /= gain
    clip_coords(coords, img0_shape)
    return coords

def clip_coords(boxes, img_shape):
    # Clip bounding xyxy bounding boxes to image shape (height, width)
    boxes[:, 0].clamp_(0, img_shape[1])  # x1
    boxes[:, 1].clamp_(0, img_shape[0])  # y1
    boxes[:, 2].clamp_(0, img_shape[1])  # x2
    boxes[:, 3].clamp_(0, img_shape[0])  # y2

class YOLOv5Detector(object):
    @classmethod
    def from_config(cls, config):
        target_size = config.YOLO_TARGET_SIZE
        padding_color = config.YOLO_PADDING_COLOR
        conf_thres = config.YOLO_THRESHOLD_CONF
        iou_thres = config.YOLO_THRESHOLD_IOU
        device = torch.device(config.YOLO_DEVICE)
        net_conf = config.YOLO_NET_CONF
        weight_path = config.YOLO_WEIGHT_PATH
        classes = config.YOLO_CLASSES
        # ----------------------------------------
        return cls(target_size, padding_color, conf_thres, iou_thres, device, net_conf, weight_path, classes)

    def __init__(self, target_size, padding_color, conf_thres, iou_thres, device, net_conf, weight_path, classes):
        self._target_size = target_size
        self._padding_color = padding_color
        self._conf_thres = conf_thres
        self._iou_thres = iou_thres
        # ----------------------------------------
        self._device = torch.device(device)
        # ----------------------------------------
        # Load model
        device = select_device(device)
        self._model = DetectMultiBackend(weight_path, device=device, dnn=False, data=ROOT / 'data/coco128.yaml', fp16=True)

        self._classes = classes
        num_classes = len(self._classes)
        hsv_tuples = [(1.0 * x / num_classes, 1., 1.) for x in range(num_classes)]
        colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
        self._colors = list(map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)), colors))

    def __call__(self, *args, **kwargs):
        return self.det(*args, **kwargs)

    def det(self, image_list: list, *args, **kwargs):
        stride, names, pt = self._model.stride, self._model.names, self._model.pt
        imgsz = check_img_size((640, 640), s=stride)  # check image size
        bs = 1  # batch_size
        vid_path, vid_writer = [None] * bs, [None] * bs
        # Run inference
        self._model.warmup(imgsz=(1 if pt or self._model.triton else bs, 3, *imgsz))  # warmup
        seen, windows, dt = 0, [], (Profile(), Profile(), Profile())
        batch, batch_image_size = self._preprocess(image_list)
        # ----------------------------------------
        batch_output = self._model(batch, augment=False)
        batch_pred = non_max_suppression(
            batch_output,
            conf_thres=self._conf_thres, iou_thres=self._iou_thres,
            classes=None, agnostic=False
        )
        # ----------------------------------------
        return self._postprocess(batch_pred, batch.shape[-2:], batch_image_size)

    def get_color(self, class_id):
        return self._colors[class_id]

    def get_class_name(self, class_id):
        return self._classes[class_id]

    def _preprocess(self, image_list: list) -> tuple:
        batch_image_tensors = []
        batch_image_size = []
        for image in image_list:
            image_shape = image.shape[:2]
            batch_image_size.append(image_shape)
            scala_ratio = min((self._target_size[0]/image_shape[0]),
                              (self._target_size[1]/image_shape[1]))
            scala_ratio = min(scala_ratio, 1.0)
            image_scaled_shape = (int(round(image_shape[0] * scala_ratio)),
                                  int(round(image_shape[1] * scala_ratio)))
            image_scaled = image
            if image_scaled_shape != image_shape:
                image_scaled = cv2.resize(image, image_scaled_shape[::-1],
                                          interpolation=cv2.INTER_LINEAR)
            # ------------------------------
            delta_height, delta_width = (self._target_size[0]-image_scaled_shape[0],
                                         self._target_size[1]-image_scaled_shape[1])
            delta_height, delta_width = numpy.mod(delta_height, 64),\
                                        numpy.mod(delta_width, 64)
            delta_height, delta_width = delta_height/2, delta_width/2
            top, bottom = int(round(delta_height-0.1)), int(round(delta_height+0.1))
            left, right = int(round(delta_width - 0.1)), int(round(delta_width + 0.1))
            image_padded = cv2.copyMakeBorder(image_scaled, top, bottom, left, right,
                                              cv2.BORDER_CONSTANT, value=self._padding_color)
            # ------------------------------
            image_torch_format = cv2.cvtColor(image_padded, cv2.COLOR_BGR2RGB)\
                                    .transpose(2, 0, 1)
            image_torch_format = numpy.ascontiguousarray(image_torch_format)
            image_tensor = torch.from_numpy(image_torch_format).to(self._device)
            image_tensor = image_tensor.half()
            image_tensor /= 255.0
            image_unsqueezed = image_tensor.unsqueeze(0)
            batch_image_tensors.append(image_unsqueezed)
        # ----------------------------------------
        batch = torch.cat(batch_image_tensors, 0)
        return batch, batch_image_size

    def _postprocess(self, batch_pred, input_image_shape, batch_image_size):
        results = []
        for idx, (pred_item, image_size) in enumerate(zip(batch_pred, batch_image_size)):
            result_item = []
            if (pred_item is not None) and len(pred_item):
                pred_item[:, :4] = scale_coords(
                    input_image_shape, pred_item[:, :4], image_size).round()
                for *p1p2, conf, klass_idx in pred_item:
                    klass_id = int(klass_idx.item())
                    klass_name = self._classes[klass_id]
                    x1, y1, x2, y2 = p1p2
                    x1, y1, x2, y2 = int(x1.item()), int(y1.item()),\
                                     int(x2.item()), int(y2.item())
                    xo, yo, w, h = round((x1+x2)/2), round((y1+y2)/2), (x2-x1), (y2-y1)
                    score = round(conf.item(), 2)
                    result_item.append((klass_name, score, (x1, y1, x2, y2), (xo, yo, w, h)))
            results.append(result_item)
        return results

