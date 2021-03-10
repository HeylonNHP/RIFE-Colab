from str2bool import *
import argparse
parser = argparse.ArgumentParser(description='Interpolation for video input')
parser.add_argument('-i', dest='inputFile', type=str, default=None)
parser.add_argument('-if', dest='interpolationFactor', type=int, default=2)
parser.add_argument('-loop', dest='loopable', type=str2bool, default=False)
parser.add_argument('-mode', dest='mode', type=int, default=3)
parser.add_argument('-crf', dest='crfout', type=int, default=20)
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

import os
import sys
import addInstalldirToPath
from Globals.EncoderConfig import EncoderConfig

# Why should we need to add the submodule to the path, just for the RIFE import to work
# Thanks for being consistently terrible, python
sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')
print(sys.path)

from generalInterpolationProceedures import *
#setupRIFE(os.getcwd(),args.gpuid)
selectedGPUs = str(args.gpuid).split(",")
selectedGPUs = [int(i) for i in selectedGPUs]

setGPUinterpolationOptions(args.batchSize,selectedGPUs)

encoderConfig = EncoderConfig()
encoderConfig.setEncodingCRF(float(args.crfout))
if bool(args.useNvenc):
    encoderConfig.enableNvenc(True)
    encoderConfig.setEncodingPreset('slow')
encoderConfig.setNvencGPUID(selectedGPUs[0])

interpolatorConfig = InterpolatorConfig()

interpolatorConfig.setMode(args.mode)
interpolatorConfig.setClearPngs(args.clearpngs)
interpolatorConfig.setLoopable(args.loopable)

interpolatorConfig.setInterpolationFactor(args.interpolationFactor)
interpolatorConfig.setMpdecimateSensitivity(args.mpdecimateSensitivity)

interpolatorConfig.setNonlocalPngs(args.nonlocalpngs)
interpolatorConfig.setScenechangeSensitivity(args.scenechangeSensitivity)

performAllSteps(args.inputFile, interpolatorConfig, encoderConfig, args.autoencode, args.blocksize)