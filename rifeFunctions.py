# @title Step 2 - Run to setup RIFE (Mandatory)
from googleDriveDownloader import *
import shutil
import glob
import os

def downloadRIFE(installPath,onWindows):
    # Run if not previously setup
    os.chdir(installPath)
    os.system(r'git clone https://github.com/hzwer/arXiv2020-RIFE')
    download_file_from_google_drive('11l8zknO1V5hapv2-Ke4DG9mHyBomS0Fc', 'RIFE_trained_model_new.zip')
    sevenZip = "7z"
    if onWindows:
        sevenZip = r"C:\Program Files\7-Zip\7z.exe"

    os.system(sevenZip + r' e RIFE_trained_model_new.zip -aoa')

    if not os.path.exists(installPath + '/arXiv2020-RIFE/train_log'):
        os.mkdir(installPath + '/arXiv2020-RIFE/train_log')
    for data in glob.glob("*.pkl"):
        shutil.move(data, installPath + "/arXiv2020-RIFE/train_log/")
    os.chdir(installPath + '/arXiv2020-RIFE/')
    shutil.rmtree(installPath+"/RIFE_trained_model_new.zip")


os.chdir('../arXiv2020-RIFE/')
import os
import cv2
import torch
import argparse
from torch.nn import functional as F
from model.RIFE_HD import Model
import numpy as np
from queue import Queue
import gc

device = None
model = None
def setupRIFE(installPath, GPUID):
    try:
        torch.cuda.set_device(GPUID)
    except:
        pass
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if torch.cuda.is_available():
        torch.set_grad_enabled(False)
        torch.backends.cudnn.enabled = True
        torch.backends.cudnn.benchmark = True
    else:
        print("WARNING: CUDA is not available, RIFE is running on CPU! [ff:nocuda-cpu]")

    model = Model()
    model.load_model('./train_log', -1)
    model.eval()
    model.device()

import time


def rifeInterpolate(img0path, img1path, outputPath, scenechangeSensitivity=0.2):
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
    img0 = F.pad(img0, padding)
    img1 = F.pad(img1, padding)

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
    saved = cv2.imwrite(outputPath, item[:, :, ::1])
    # print("Saved", saved)

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
    # torch.cuda.empty_cache()