import os
#os.chdir('arXiv2020-RIFE/')
import shutil
import cv2
import torch
import argparse
from torch.nn import functional as F
from arXiv2020RIFE.model.RIFE_HD import Model
import numpy as np
from queue import Queue
import gc
import threading
from QueuedFrames.FrameFile import FrameFile

setupRifeThreadLock = threading.Lock()

def setupRIFE(installPath, GPUID):
    with setupRifeThreadLock:
        try:
            torch.cuda.set_device(GPUID)
        except:
            pass
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        if torch.cuda.is_available():
            torch.set_grad_enabled(False)
            torch.backends.cudnn.enabled = True
            torch.backends.cudnn.benchmark = True
            #torch.set_default_tensor_type(torch.HalfTensor)
        else:
            print("WARNING: CUDA is not available, RIFE is running on CPU! [ff:nocuda-cpu]")

        model = Model()
        model.load_model(installPath + os.path.sep + 'arXiv2020RIFE' + os.path.sep + 'train_log', -1)
        model.eval()
        model.device()
        return device,model

import time


def rifeInterpolate(device,model,img0path, img1path, outputPath, scenechangeSensitivity=0.2):
    img0 = cv2.imread(img0path)
    img1 = cv2.imread(img1path)

    h, w, _ = img0.shape
    imgList = [img0, img1]

    imgs = torch.from_numpy(np.transpose(imgList, (0, 3, 1, 2))).to(device, non_blocking=True).float() / 255.
    img0 = imgs[:-1]
    img1 = imgs[1:]

    ph = ((h - 1) // 64 + 1) * 64
    pw = ((w - 1) // 64 + 1) * 64
    padding = (0, pw - w, 0, ph - h)
    p = (F.interpolate(img0, (16, 16), mode='bilinear', align_corners=False)
         - F.interpolate(img1, (16, 16), mode='bilinear', align_corners=False)).abs().mean()
    img0 = F.pad(img0, padding).half()
    img1 = F.pad(img1, padding).half()

    mid = None
    if p > scenechangeSensitivity:
        mid = img0
    else:
        mid = model.inference(img0, img1, True)

    inferences = [mid]
    inferences = list(
        map(lambda x: ((x[:, :, :h, :w] * 255.).byte().cpu().detach().numpy().transpose(0, 2, 3, 1)), inferences))
    buffer = Queue()
    for i in range(inferences[0].shape[0]):
        buffer.put(inferences[0][i])
    item = buffer.get()
    #saved = cv2.imwrite(outputPath, item[:, :, ::1],[cv2.IMWRITE_PNG_COMPRESSION, 6])
    saved = cv2.imwrite(outputPath, item[:, :, ::1])
    # print("Saved", saved)

def rifeInterpolate2(device, model, img0frame:FrameFile, img1frame:FrameFile, outputFrame:FrameFile, scenechangeSensitivity=0.2):
    img0 = img0frame.getImageData()
    img1 = img1frame.getImageData()

    h, w, _ = img0.shape
    imgList = [img0, img1]

    imgs = torch.from_numpy(np.transpose(imgList, (0, 3, 1, 2))).to(device, non_blocking=True).float() / 255.
    img0 = imgs[:-1]
    img1 = imgs[1:]

    ph = ((h - 1) // 64 + 1) * 64
    pw = ((w - 1) // 64 + 1) * 64
    padding = (0, pw - w, 0, ph - h)
    p = (F.interpolate(img0, (16, 16), mode='bilinear', align_corners=False)
         - F.interpolate(img1, (16, 16), mode='bilinear', align_corners=False)).abs().mean()
    img0 = F.pad(img0, padding)#.half()
    img1 = F.pad(img1, padding)#.half()

    mid = None
    if p > scenechangeSensitivity:
        mid = img0
    else:
        mid = model.inference(img0, img1, True)

    inferences = [mid]
    inferences = list(
        map(lambda x: ((x[:, :, :h, :w] * 255.).byte().cpu().detach().numpy().transpose(0, 2, 3, 1)), inferences))
    buffer = Queue()
    for i in range(inferences[0].shape[0]):
        buffer.put(inferences[0][i])
    item = buffer.get()

    outputFrame.setImageData(item[:, :, ::1])
    return outputFrame
    # print("Saved", saved)

'''
def rifeInterpolatePNGfolder(inputFolder, outputFolder):
    if inputFolder[-1] != '/':
        inputFolder = inputFolder + '/'
    if outputFolder[-1] != '/':
        outputFolder = outputFolder + '/'

    if not os.path.exists(outputFolder):
        os.mkdir(outputFolder)

    files = os.listdir(inputFolder)
    files.sort()

    fileCount = 1
    shutil.copy(inputFolder + files[0], outputFolder + '{:06d}.png'.format(fileCount))
    fileCount += 1
    for i in range(0, len(files) - 1):
        fullFile = inputFolder + files[i]
        print(fullFile, '(' + str(len(files) - 1) + ')', '-', "{:.2f}%".format((i / (len(files) - 1)) * 100))
        rifeInterpolate(inputFolder + files[i], inputFolder + files[i + 1],
                        outputFolder + '{:06d}.png'.format(fileCount))

        fileCount += 1
        shutil.copy(inputFolder + files[i + 1], outputFolder + '{:06d}.png'.format(fileCount))
        fileCount += 1
    # del model
    # gc.collect()
    # torch.cuda.empty_cache()'''