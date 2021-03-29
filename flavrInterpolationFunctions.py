import os
import sys
from googleDriveDownloader import *
import torchvision

sys.path.insert(0, os.getcwd() + os.path.sep + 'FLAVR')
print(sys.path)

def downloadFLAVRmodel(installPath):
    FLAVRfolder = installPath + os.path.sep + 'FLAVR'
    FLAVRmodelPath = FLAVRfolder + os.path.sep + 'FLAVR_2x.pth'
    try:
        os.mkdir(FLAVRfolder)
    except:
        if not os.path.exists(FLAVRfolder):
            print("Can't make FLAVR folder")
        return
    if not os.path.exists(FLAVRmodelPath):
        download_file_from_google_drive('1XFk9YZP9llTeporF-t_Au1dI-VhDQppG', FLAVRmodelPath)
downloadFLAVRmodel(os.getcwd())

import torch
import cv2
import numpy as np
import threading
from QueuedFrames.FrameFile import FrameFile

from FLAVR.model1.FLAVR_arch import UNet_3D_3D
from FLAVR.dataset.transforms import ToTensorVideo , Resize

model_name = "unet_18"
n_outputs = 2 - 1
joinType = "concat"
up_mode = "transpose"
nbr_frame = 4

useHalfPrecision: bool = False
setupFLAVRthreadLock = threading.Lock()

def setupFLAVR(installPath, GPUID):
    global useHalfPrecision
    device = None
    with setupFLAVRthreadLock:
        try:
            torch.cuda.set_device(GPUID)
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        except:
            pass

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

    model = UNet_3D_3D(model_name.lower(), n_inputs=4, n_outputs=n_outputs, joinType=joinType, upmode=up_mode)
    saved_state_dict = torch.load(installPath + os.path.sep + 'FLAVR' + os.path.sep + 'FLAVR_2x.pth')['state_dict']
    saved_state_dict = {k.partition("module.")[-1]: v for k, v in saved_state_dict.items()}
    model.load_state_dict(saved_state_dict)
    model = model.cuda(device)

    model = model.eval()
    return device,model

def FLAVRinterpolat(device, model, img0frame: FrameFile, img1frame: FrameFile, outputFrame: FrameFile,
                    scenechangeSensitivity=0.2, scale=0.5):
    global useHalfPrecision
    img0 = img0frame.getImageData()
    img1 = img1frame.getImageData()

    imgList = [img0,img1]

    width = int(imgList[0].shape[1])
    height = int(imgList[0].shape[0])

    downscale = int(1 * 8)
    resizes = (8 * (width // downscale), 8 * (height // downscale))
    for i in range(0,len(imgList)):
        imgList[i] = cv2.resize(imgList[i],resizes, interpolation = cv2.INTER_AREA)

    imgList = [imgList[0],imgList[0],imgList[1],imgList[1]]

    images = [torch.Tensor(np.asarray(f)).type(torch.uint8) for f in imgList]
    videoTensor = torch.stack(images)

    idxs = torch.Tensor(range(len(videoTensor))).type(torch.long).view(1, -1).unfold(1, size=nbr_frame, step=1).squeeze(0)
    videoTensor, resizes = video_transform(videoTensor, 1)

    frames = torch.unbind(videoTensor, 1)

    #print(frames)
    idxSet = idxs[0]
    inputs = [frames[idx_].cuda().unsqueeze(0) for idx_ in idxSet]

    output = None
    with torch.no_grad():
        output = model(inputs)

    #print("OUTPUT LEN",len(output))

    output = output[0].squeeze(0).cpu().data

    #return outputFrame

    '''imgList = [img0, img1]
    imgs = torch.from_numpy(np.transpose(imgList, (3, 0, 1, 2))).to(device, non_blocking=True).float() / 255.

    img0 = imgs[:-1].unsqueeze(0)
    img1 = imgs[1:].unsqueeze(0)'''

    '''img0 = (torch.tensor(img0.transpose(1, 2, 0)).to(device) / 255.).unsqueeze(0)
    img1 = (torch.tensor(img1.transpose(1, 2, 0)).to(device) / 255.).unsqueeze(0)'''

    '''T , H , W = img0.size(0), img0.size(1) , img0.size(2)
    print(T,H,W)

    output = model((img0,img1))

    output = [of.squeeze(0).cpu().data for of in outputFrame]'''

    q_im = output.data.mul(255.).clamp(0, 255).round()
    im = q_im.permute(1, 2, 0).cpu().numpy().astype(np.uint8)
    # im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
    im = cv2.resize(im,(width,height), interpolation = cv2.INTER_AREA)
    outputFrame.setImageData(im)
    return outputFrame


def video_transform(videoTensor, downscale=1):
    T, H, W = videoTensor.size(0), videoTensor.size(1), videoTensor.size(2)

    downscale = int(downscale * 8)
    resizes = 8 * (H // downscale), 8 * (W // downscale)
    #resizes = H,W
    #transforms = torchvision.transforms.Compose([ToTensorVideo(), Resize(resizes)])
    transforms = torchvision.transforms.Compose([ToTensorVideo()])
    videoTensor = transforms(videoTensor)

    # resizes = 720,1280
    #print("Resizing to %dx%d" % (resizes[0], resizes[1]))
    return videoTensor, resizes

def nog():
    device,model = setupFLAVR(r"C:\Users\Heylon\Documents\RIFEstuff\RIFE-Colab",1)

    img0 = FrameFile(r"C:\Users\Heylon\Desktop\Videos\diives1\original_frames\000000000004100.png")

    img1 = FrameFile(r"C:\Users\Heylon\Desktop\Videos\diives1\original_frames\000000000008360.png")

    img2 = FrameFile(r"C:\Users\Heylon\Desktop\Videos\diives1\original_frames\000000000012460.png")

    img0.loadImageData()
    img2.loadImageData()

    img1 = FLAVRinterpolat(device,model,img0,img2,img1)

    img1.saveImageData()

#nog()