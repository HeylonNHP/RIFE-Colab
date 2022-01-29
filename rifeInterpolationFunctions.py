import os
import threading

import numpy as np
# os.chdir('arXiv2020-RIFE/')
import torch
# from arXiv2020RIFE.model.RIFE_HDv2 import Model
from arXiv2020RIFE.train_log.RIFE_HDv3 import Model
from torch.nn import functional as F

from QueuedFrames.FrameFile import FrameFile

useHalfPrecision: bool = False

setupRifeThreadLock = threading.Lock()


def setup_rife(install_path, gpu_id):
    global useHalfPrecision
    with setupRifeThreadLock:
        try:
            # TODO: Potentially use model.Device instead? (Line 41)
            torch.cuda.set_device(gpu_id)
        except:
            print("Could net set CUDA device. Attempted CUDA device:", gpu_id)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if torch.cuda.is_available():
            torch.set_grad_enabled(False)
            torch.backends.cudnn.enabled = True
            torch.backends.cudnn.benchmark = True
            if useHalfPrecision:
                torch.set_default_tensor_type(torch.HalfTensor)
            else:
                torch.set_default_tensor_type(torch.FloatTensor)
        else:
            print("WARNING: CUDA is not available, RIFE is running on CPU! [ff:nocuda-cpu]")

        model = Model()
        model.load_model(install_path + os.path.sep + 'arXiv2020RIFE' + os.path.sep + 'train_log', -1)
        model.eval()
        model.device()
        return device, model


def rife_interpolate(device, model, img0frame: FrameFile, img1frame: FrameFile, output_frame: FrameFile,
                     scenechange_sensitivity=0.2, scale=0.5):
    global useHalfPrecision
    img0 = img0frame.getImageData()
    img1 = img1frame.getImageData()

    h, w, _ = img0.shape
    img_list = [img0, img1]

    imgs = torch.from_numpy(np.transpose(img_list, (0, 3, 1, 2))).to(device, non_blocking=True).float() / 255.
    img0 = imgs[:-1]
    img1 = imgs[1:]

    tmp = max(32, int(32 / scale))
    ph = ((h - 1) // tmp + 1) * tmp
    pw = ((w - 1) // tmp + 1) * tmp
    padding = (0, pw - w, 0, ph - h)
    p = (F.interpolate(img0, (16, 16), mode='bilinear', align_corners=False)
         - F.interpolate(img1, (16, 16), mode='bilinear', align_corners=False)).abs().mean()
    if useHalfPrecision:
        img0 = F.pad(img0, padding).half()
        img1 = F.pad(img1, padding).half()
    else:
        img0 = F.pad(img0, padding)
        img1 = F.pad(img1, padding)

    if p > scenechange_sensitivity:
        mid = img0
    else:
        mid = model.inference(img0, img1, scale)

    item = (mid[:, :, :h, :w] * 255.).byte().cpu().detach().numpy().transpose(0, 2, 3, 1)[0]
    output_frame.setImageData(item)
    return output_frame


def set_use_half_precision(enable: bool):
    global useHalfPrecision
    useHalfPrecision = enable
