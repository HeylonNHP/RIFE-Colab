from str2bool import *
import argparse
parser = argparse.ArgumentParser(description='Interpolation for video input')
parser.add_argument('-i', dest='inputDirectory', type=str, default=None)
parser.add_argument('-mode', dest='mode', type=int, default=3)
parser.add_argument('-fpstarget', dest='fpsTarget', type=float, default=59)
parser.add_argument('-crf', dest='crf', type=float, default=20)
parser.add_argument('-clearpngs', dest='clearpngs', type=str2bool, default=True)
parser.add_argument('-nonlocalpngs', dest='nonlocalpngs', type=str2bool, default=True)
parser.add_argument('-scenesens', dest='scenechangeSensitivity', type=float, default=0.2)
parser.add_argument('-mpdecimate', dest='mpdecimateSensitivity', type=str, default="64*12,64*8,0.33")
parser.add_argument('-usenvenc', dest='useNvenc', type=str2bool, default=False)
parser.add_argument('-gpuids', dest='gpuid', type=str, default="0")
parser.add_argument('-batch', dest='batchSize', type=int, default=1)
parser.add_argument('-autoencode', dest='autoencode', type=str2bool, default=False)
args = parser.parse_args()

print("NONLOCALPNGS",args.nonlocalpngs,"CLEARPNGS",args.clearpngs)

import os
import traceback
import sys

# Why should we need to add the submodule to the path, just for the RIFE import to work
# Thanks for being consistently terrible, python
sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')


from generalInterpolationProceedures import *

selectedGPUs = str(args.gpuid).split(",")
selectedGPUs = [int(i) for i in selectedGPUs]

setNvencSettings(selectedGPUs[0],'p7')
setGPUinterpolationOptions(args.batchSize,selectedGPUs)
# Batch interpolation code
batchInterpolateFolder(args.inputDirectory,args.mode,args.crf,args.fpsTarget,args.clearpngs,args.nonlocalpngs,
                       args.scenechangeSensitivity,args.mpdecimateSensitivity,args.useNvenc,args.autoencode)