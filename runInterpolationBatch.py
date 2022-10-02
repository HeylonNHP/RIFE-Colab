from str2bool import *
import argparse

import os
import traceback
import sys
import addInstalldirToPath

# Why should we need to add the submodule to the path, just for the RIFE import to work
# Thanks for being consistently terrible, python
sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')

from generalInterpolationProceedures import *

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
parser.add_argument('-blocksize', dest='blocksize', type=int, default=3000)
args = parser.parse_args()

print("NONLOCALPNGS", args.nonlocalpngs, "CLEARPNGS", args.clearpngs)

selectedGPUs = str(args.gpuid).split(",")
selectedGPUs = [int(i) for i in selectedGPUs]

setGPUinterpolationOptions(args.batchSize, selectedGPUs)

encoderConfig = EncoderConfig()
encoderConfig.set_encoding_crf(float(args.crf))
if bool(args.useNvenc):
    encoderConfig.enable_nvenc(True)
    encoderConfig.set_encoding_preset('slow')
encoderConfig.set_nvenc_gpu_id(selectedGPUs[0])

interpolatorConfig = InterpolatorConfig()

interpolatorConfig.setMode(args.mode)
interpolatorConfig.setClearPngs(args.clearpngs)
encoderConfig.set_looping_options(10, 15, True)

interpolatorConfig.setMpdecimateSensitivity(args.mpdecimateSensitivity)

interpolatorConfig.setNonlocalPngs(args.nonlocalpngs)
interpolatorConfig.setScenechangeSensitivity(args.scenechangeSensitivity)

interpolatorConfig.setMode3TargetFPS(True, 60)

interpolatorConfig.setBackupThreadStartLimit(10)

# Batch interpolation code
batchInterpolateFolder(args.inputDirectory, interpolatorConfig, args.fpsTarget, encoderConfig, args.autoencode,
                       args.blocksize)
