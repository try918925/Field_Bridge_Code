
from utils.torch_utils import select_device
from utils.general import check_img_size
from utils.augmentations import classify_transforms

from models.common import DetectMultiBackend
from torch.nn.functional import softmax
import torch

class YOLOv5Classifier(object):
    
    @classmethod
    def from_config(cls, config):
        weight_path = config.YOLO_WEIGHT_PATH
        infer_size = config.YOLO_INFER_SIZE
        device = torch.device(config.YOLO_DEVICE)
        dnn = config.YOLO_INFER_DNN
        half = config.YOLO_INFER_HALF
        classes = config.YOLO_CLASSES
        return cls(weight_path, infer_size, device, dnn, half, classes)

    def __init__(self, weight_path, infer_size, device, dnn, half, classes):
        self._half = half
        self._classes = classes
        self._device = select_device(device) 
        self._model = DetectMultiBackend(weights= weight_path, device=self._device, \
                                         dnn= dnn, data= None, fp16= half)
        stride, names, pt = self._model.stride, self._model.names, self._model.pt
        self._names = names
        self._infer_size = check_img_size(infer_size, s=stride)  # check image size
        bs = 1  # batch_size
        self._model.warmup(imgsz=(1 if pt else bs, 3, *self._infer_size)) 
        self._transforms = classify_transforms(self._infer_size[0])

    def __call__(self, *args, **kwargs):
        return self.infer(*args, **kwargs)

    def infer(self, image_list: list, *args, **kwargs):
        batch, batch_image_size = self._preprocess(image_list)
        batch_output = self._model(batch)
        batch_pred = softmax(batch_output, dim=1)  # probabilities

        return self._postprocess(batch_pred, batch.shape[-2:], batch_image_size)

    def get_class_name(self, class_id):
        return self._classes[class_id]
    
    def _preprocess(self, image_list: list) -> tuple:
        batch_image_tensors = []
        batch_image_size = []
        for image in image_list:
            image_shape = image.shape[:2]   
            batch_image_size.append(image_shape) 
            image_tensor = self._transforms(image)
            image_tensor = torch.Tensor(image_tensor).to(self._model.device)
            image_tensor = image_tensor.half() if self._model.fp16 else image_tensor.float()  # uint8 to fp16/32
            image_unsqueezed = image_tensor.unsqueeze(0)
            batch_image_tensors.append(image_unsqueezed)
        batch = torch.cat(batch_image_tensors, 0)
        return batch, batch_image_size      

    def _postprocess(self, batch_pred, input_image_shape, batch_image_size):
        results = []
        for idx, (pred_item, image_size) in enumerate(zip(batch_pred, batch_image_size)):
            result_item = []
            if (pred_item is not None) and len(pred_item):
                top5_index = pred_item.argsort(0, descending=True)[:5].tolist()  # top 5 indices
                # for i, prob in enumerate(pred_item):  # per image
                score = round(pred_item[top5_index[0]].item(), 4)
                class_id = top5_index[0]
                class_name = self._classes[class_id]
                result_item.append((class_id, class_name, score))
            results.append(result_item)
        return results
