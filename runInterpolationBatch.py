import argparse
parser = argparse.ArgumentParser(description='Interpolation for video input')
parser.add_argument('-i', dest='inputDirectory', type=str, default=None)
parser.add_argument('-mode', dest='mode', type=int, default=3)
parser.add_argument('-fpstarget', dest='fpsTarget', type=float, default=59)
parser.add_argument('-crf', dest='crf', type=float, default=20)
parser.add_argument('-clearpngs', dest='clearpngs', type=bool, default=True)
parser.add_argument('-nonlocalpngs', dest='nonlocalpngs', type=bool, default=True)
parser.add_argument('-scenesens', dest='scenechangeSensitivity', type=float, default=0.2)
parser.add_argument('-mpdecimate', dest='mpdecimateSensitivity', type=str, default="64*12,64*8,0.33")
parser.add_argument('-usenvenc', dest='useNvenc', type=bool, default=False)
parser.add_argument('-gpuid', dest='gpuid', type=int, default=0)
args = parser.parse_args()

import os
import traceback
import sys

# Why should we need to add the submodule to the path, just for the RIFE import to work
# Thanks for being consistently terrible, python
sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')

from generalInterpolationProceedures import *
setupRIFE(os.getcwd(),args.gpuid)
setNvencSettings(args.gpuid,'p7')

# Batch interpolation code
files = []
# r=root, d=directories, f = files
for r, d, f in os.walk(args.inputDirectory):
    for file in f:
        files.append(os.path.join(r, file))

files.sort()

for inputVideoFile in files:
    try:
        print(inputVideoFile)

        if args.mode == 1 or args.mode == 3:
            currentFPS = getFPS(inputVideoFile)
        elif args.mode == 4 or args.mode == 3:
            currentFPS = getFrameCount(inputVideoFile,True) / getLength(inputVideoFile)

        # Attempt to interpolate everything to above 59fps
        targetFPS = args.fpsTarget
        exponent = 1
        if currentFPS < targetFPS:
            while (currentFPS * (2 ** exponent)) < targetFPS:
                exponent += 1
        else:
            continue
        # use [l] to denote whether the file is a loopable video
        print("looping?", '[l]' in inputVideoFile)
        if '[l]' in inputVideoFile:
            print("LOOP")
            performAllSteps(inputVideoFile,(2 ** exponent),True,args.mode,args.crf,args.clearpngs,args.nonlocalpngs,args.scenechangeSensitivity,args.mpdecimateSensitivity,args.useNvenc)
        else:
            print("DON'T LOOP")
            performAllSteps(inputVideoFile,(2 ** exponent),False,args.mode,args.crf,args.clearpngs,args.nonlocalpngs,args.scenechangeSensitivity,args.mpdecimateSensitivity,args.useNvenc)
    except:
        traceback.print_exc()
