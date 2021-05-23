import os
#os.chdir('arXiv2020-RIFE/')
import shutil
import cv2
import torch
import argparse
from torch.nn import functional as F
#from arXiv2020RIFE.model.RIFE_HDv2 import Model
from arXiv2020RIFE.train_log.RIFE_HDv3 import Model
import numpy as np
from queue import Queue
import gc
import threading
from QueuedFrames.FrameFile import FrameFile

useHalfPrecision: bool = False

setupRifeThreadLock = threading.Lock()

def setupRIFE(installPath, GPUID):
    global useHalfPrecision
    with setupRifeThreadLock:
        try:
            # TODO: Potentially use model.Device instead? (Line 41)
            torch.cuda.set_device(GPUID)
        except:
            print("Could net set CUDA device. Attempted CUDA device:",GPUID)
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
        model.load_model(installPath + os.path.sep + 'arXiv2020RIFE' + os.path.sep + 'train_log', -1)
        model.eval()
        model.device()
        return device,model


def rifeInterpolate(device, model, img0frame: FrameFile, img1frame: FrameFile, outputFrame: FrameFile,
                    scenechangeSensitivity=0.2, scale=0.5):
    global useHalfPrecision
    img0 = img0frame.getImageData()
    img1 = img1frame.getImageData()

    h, w, _ = img0.shape
    imgList = [img0, img1]

    imgs = torch.from_numpy(np.transpose(imgList, (0, 3, 1, 2))).to(device, non_blocking=True).float() / 255.
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

    mid = None
    if p > scenechangeSensitivity:
        mid = img0
    else:
        mid = model.inference(img0, img1, scale)

    item = (mid[:, :, :h, :w] * 255.).byte().cpu().detach().numpy().transpose(0, 2, 3, 1)[0]
    outputFrame.setImageData(item)
    return outputFrame

def setUseHalfPrecision(enable:bool):
    global useHalfPrecision
    useHalfPrecision = enable
