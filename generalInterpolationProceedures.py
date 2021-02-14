import math
import os
import shutil
import traceback
from queue import Queue
import threading

from QueuedFrames.SaveFramesList import SaveFramesList
from QueuedFrames.queuedFrameList import *
from QueuedFrames.queuedFrame import *
from QueuedFrames.FrameFile import *
import autoEncoding

from runAndPrintOutput import runAndPrintOutput
from FFmpegFunctions import *
from frameChooser import chooseFrames
from Globals.GlobalValues import GlobalValues
from EventHandling import Event

import warnings
warnings.filterwarnings("ignore")

FFMPEG4 = GlobalValues().getFFmpegPath()
GPUID = 0
nvencPreset = 'p7'
installPath = os.getcwd()
print('INSTALL:', installPath)

# Check if running on Windows or not
onWindows = None
if os.name == 'nt':
    onWindows = True
else:
    onWindows = False

# Get and initialise RIFE
from rifeFunctions import downloadRIFE

downloadRIFE(installPath, onWindows)
os.chdir(installPath)
from rifeInterpolationFunctions import *

gpuBatchSize = 2
gpuIDsList = [0]

interpolationProgressUpdate = Event.Event()
currentSavingPNGRanges:list = []

def subscribeTointerpolationProgressUpdate(function):
    interpolationProgressUpdate.append(function)


def setFFmpeg4Path(path):
    global FFMPEG4
    FFMPEG4 = path
    setFFmpegLocation(FFMPEG4)


def setNvencSettings(nvencGpuID, preset):
    global GPUID
    global nvencPreset
    GPUID = nvencGpuID
    nvencPreset = preset


def setGPUinterpolationOptions(batchSize: int, _gpuIDsList: list):
    global gpuIDsList
    global gpuBatchSize
    gpuIDsList = _gpuIDsList
    gpuBatchSize = batchSize




def extractFrames(inputFile, projectFolder, mode, mpdecimateSensitivity="64*12,64*8,0.33"):
    '''
    Equivalent to DAINAPP Step 1
    '''
    os.chdir(projectFolder)
    if os.path.exists("original_frames"):
        shutil.rmtree("original_frames")
    if not os.path.exists("original_frames"):
        os.mkdir("original_frames")

    if mode == 1:
        runAndPrintOutput(
            [FFMPEG4, '-i', inputFile, '-map_metadata', '-1', '-pix_fmt', 'rgb24', 'original_frames/%15d.png'])
    elif mode == 3 or mode == 4:
        hi, lo, frac = mpdecimateSensitivity.split(",")
        mpdecimate = "mpdecimate=hi={}:lo={}:frac={}".format(hi, lo, frac)
        runAndPrintOutput(
            [FFMPEG4, '-i', inputFile, '-map_metadata', '-1', '-pix_fmt', 'rgb24', '-copyts', '-r', str(GlobalValues.timebase), '-vsync',
             '0', '-frame_pts', 'true', '-vf', mpdecimate, '-qscale:v', '1', 'original_frames/%15d.png'])


def runInterpolator(inputFile, projectFolder, interpolationFactor, loopable, mode, scenechangeSensitivity, outputFPS):
    '''
    Equivalent to DAINAPP Step 2
    :param outputFPS:
    '''
    global gpuIDsList
    global gpuBatchSize
    os.chdir(installPath + '/arXiv2020RIFE/')
    origFramesFolder = projectFolder + '/' + "original_frames"
    interpFramesFolder = projectFolder + '/' + "interpolated_frames"

    if not os.path.exists(interpFramesFolder):
        os.mkdir(interpFramesFolder)

    # Loopable
    if loopable:
        generateLoopContinuityFrame(origFramesFolder)

    files = os.listdir(origFramesFolder)
    files.sort()

    framesQueue = Queue()

    if mode == 1:

        count = 0
        shutil.copy(origFramesFolder + '/' + files[0], interpFramesFolder + '/' + '{:015d}.png'.format(count))

        for i in range(0, len(files) - 1):
            framesList: list = []

            progressMessage = "Interpolating frame: {} Of {} {:.2f}%".format(i + 1, len(files),
                                                                             ((i + 1) / len(files)) * 100)

            queuedFrameList: QueuedFrameList = QueuedFrameList(framesList,
                                                               origFramesFolder + '/' + files[i],
                                                               interpFramesFolder + '/' + '{:015d}.png'.format(count),
                                                               origFramesFolder + '/' + files[i + 1],
                                                               interpFramesFolder + '/' + '{:015d}.png'.format(
                                                                   count + interpolationFactor))

            interpolationProgress = InterpolationProgress()
            interpolationProgress.progressMessage = progressMessage
            interpolationProgress.completedFrames = i+1
            interpolationProgress.totalFrames = len(files)
            queuedFrameList.interpolationProgress = interpolationProgress

            currentFactor = interpolationFactor

            while currentFactor > 1:
                period = int(interpolationFactor / currentFactor)
                for j in range(0, period):
                    offset = int(currentFactor * j)
                    beginFrame = interpFramesFolder + '/' + '{:015d}.png'.format(count + offset)
                    endFrame = interpFramesFolder + '/' + '{:015d}.png'.format(count + currentFactor + offset)
                    middleFrame = interpFramesFolder + '/' + '{:015d}.png'.format(
                        count + int(currentFactor / 2) + offset)

                    framesList.append(QueuedFrame(beginFrame, endFrame, middleFrame, scenechangeSensitivity))
                currentFactor = int(currentFactor / 2)

            count += interpolationFactor
            framesQueue.put(queuedFrameList)

    elif mode == 3 or mode == 4:
        count = 0
        shutil.copy(origFramesFolder + '/' + files[0], interpFramesFolder + '/' + '{:015d}.png'.format(count))
        # To ensure no duplicates on the output with the new VFR to CFR algorithm, double the interpolation factor. TODO: Investigate
        modeModOutputFPS = outputFPS
        #if mode == 3:
        interpolationFactor = interpolationFactor * 2
        modeModOutputFPS = modeModOutputFPS * 2

        for i in range(0, len(files) - 1):
            framesList: list = []

            localInterpolationFactor = interpolationFactor
            # If mode 3, calculate interpolation factor on a per-frame basis to maintain desired FPS

            beginFrameTime = int(files[i][:-4])
            endFrameTime = int(files[i + 1][:-4])
            timeDiff = endFrameTime - beginFrameTime
            if mode == 3:
                localInterpolationFactor = 2

                while 1 / (((endFrameTime - beginFrameTime) / localInterpolationFactor) / GlobalValues.timebase) < modeModOutputFPS:
                    localInterpolationFactor = int(localInterpolationFactor * 2)

            progressMessage = "Interpolating frame: {} Of {} {:.2f}% Frame interp. factor {}x".format(i + 1, len(files),
                                                                                                      ((i + 1) / len(
                                                                                                          files)) * 100,
                                                                                                      localInterpolationFactor)
            # Get timecodes of both working frames
            currentTimecode = int(files[i][:-4])
            nextTimecode = int(files[i + 1][:-4])

            queuedFrameList: QueuedFrameList = QueuedFrameList(framesList,
                                                               origFramesFolder + '/' + files[i],
                                                               interpFramesFolder + '/' + '{:015d}.png'.format(
                                                                   currentTimecode),
                                                               origFramesFolder + '/' + files[i + 1],
                                                               interpFramesFolder + '/' + '{:015d}.png'.format(
                                                                   nextTimecode))

            interpolationProgress = InterpolationProgress()
            interpolationProgress.progressMessage = progressMessage
            interpolationProgress.completedFrames = i+1
            interpolationProgress.totalFrames = len(files)
            queuedFrameList.interpolationProgress = interpolationProgress

            currentFactor = localInterpolationFactor

            while currentFactor > 1:
                period = int(round(localInterpolationFactor / currentFactor))
                for j in range(0, period):
                    # Get offset from the first frame
                    offset = (timeDiff / period) * j
                    # print(currentTimecode,offset, "j ",j)
                    # Time difference between 'begin' and 'end' frames relative to current interpolation factor (Block size)
                    currentFactor2 = (currentFactor / localInterpolationFactor) * timeDiff
                    beginFrameTime = int(currentTimecode + offset)
                    endFrameTime = int(currentTimecode + currentFactor2 + offset)
                    middleFrameTime = int(currentTimecode + (currentFactor2 / 2) + offset)

                    beginFrame = interpFramesFolder + '/' + '{:015d}.png'.format(beginFrameTime)
                    endFrame = interpFramesFolder + '/' + '{:015d}.png'.format(endFrameTime)
                    middleFrame = interpFramesFolder + '/' + '{:015d}.png'.format(middleFrameTime)

                    framesList.append(QueuedFrame(beginFrame, endFrame, middleFrame, scenechangeSensitivity))
                currentFactor = int(currentFactor / 2)

            # count += interpolationFactor
            framesQueue.put(queuedFrameList)

    inFramesList: list = []
    loadPNGThread = threading.Thread(target=queueThreadLoadFrame,args=(origFramesFolder,inFramesList,))
    loadPNGThread.start()

    outFramesQueue: Queue = Queue(maxsize=128)
    gpuList: list = gpuIDsList
    batchSize: int = gpuBatchSize
    threads: list = []
    for i in range(0, batchSize):
        for gpuID in gpuList:
            rifeThread = threading.Thread(target=queueThreadInterpolator, args=(framesQueue, outFramesQueue, inFramesList, gpuID,))
            threads.append(rifeThread)
            rifeThread.start()
        time.sleep(5)

    saveThreads = []
    for i in range(0, batchSize):
        saveThread = threading.Thread(target=queueThreadSaveFrame, args=(outFramesQueue,))
        saveThreads.append(saveThread)
        saveThread.start()

    # Wait for interpolation threads to exit
    for rifeThread in threads:
        rifeThread.join()

    # If all threads crashed before the end of interpolation - TODO: Cycle through all GPUs
    while not framesQueue.empty():
        print("Starting backup thread")
        rifeThread = threading.Thread(target=queueThreadInterpolator, args=(framesQueue, outFramesQueue, inFramesList, gpuID,))
        rifeThread.start()
        time.sleep(5)
        rifeThread.join()

    # Wait for loading thread to exit
    loadPNGThread.join()

    # Interpolation done, ask save threads to exit and wait for them
    print("Put none - ask save thread to quit")
    outFramesQueue.put(None)

    for saveThread in saveThreads:
        saveThread.join()

    # Loopable
    if loopable:
        removeLoopContinuityFrame(interpFramesFolder)

    # Raise event, interpolation finished
    interpolationProgress = InterpolationProgress()
    interpolationProgress.completedFrames = len(files)
    interpolationProgress.totalFrames = len(files)
    interpolationProgress.progressMessage = "Interpolation finished"
    interpolationProgressUpdate(interpolationProgress)

    return [outputFPS]

inFrameGetLock = threading.Lock()

def queueThreadInterpolator(framesQueue: Queue, outFramesQueue: Queue, inFramesList:list, gpuid):
    device, model = setupRIFE(installPath, gpuid)
    while True:
        listOfCompletedFrames = []
        if framesQueue.empty():
            freeVRAM(model,device)
            break
        currentQueuedFrameList: QueuedFrameList = framesQueue.get()
        print(currentQueuedFrameList.interpolationProgress.progressMessage)
        # Raise event
        interpolationProgressUpdate(currentQueuedFrameList.interpolationProgress)
        listOfAllFramesInterpolate: list = currentQueuedFrameList.frameList

        # Copy start and end files
        if not os.path.exists(currentQueuedFrameList.startFrameDest):
            shutil.copy(currentQueuedFrameList.startFrame, currentQueuedFrameList.startFrameDest)
        if not os.path.exists(currentQueuedFrameList.endFrameDest):
            shutil.copy(currentQueuedFrameList.endFrame, currentQueuedFrameList.endFrameDest)
        try:
            for frame in listOfAllFramesInterpolate:
                queuedFrame: QueuedFrame = frame
                success = False

                # Load begin frame from HDD or RAM
                beginFrame = None
                # If the current frame pair uses an original_frame - Then grab it from RAM
                if queuedFrame.beginFrame == currentQueuedFrameList.startFrameDest:
                    with inFrameGetLock:
                        for i in range(0,len(inFramesList)):
                            if currentQueuedFrameList.startFrame == str(inFramesList[i]):
                                beginFrame = inFramesList[i]
                                break

                if beginFrame is None:
                    for i in range(0, len(listOfCompletedFrames)):
                        if str(listOfCompletedFrames[i]) == queuedFrame.beginFrame:
                            beginFrame = listOfCompletedFrames[i]
                            break
                if beginFrame is None:
                    beginFrame = FrameFile(queuedFrame.beginFrame)
                    beginFrame.loadImageData()

                # Load end frame from HDD or RAM
                endFrame = None
                # If the current frame pair uses an original_frame - Then grab it from RAM
                if queuedFrame.endFrame == currentQueuedFrameList.endFrameDest:
                    with inFrameGetLock:
                        for i in range(0,len(inFramesList)):
                            if currentQueuedFrameList.endFrame == str(inFramesList[i]):
                                endFrame = inFramesList[i]
                                break


                if endFrame is None:
                    for i in range(0, len(listOfCompletedFrames)):
                        if str(listOfCompletedFrames[i]) == queuedFrame.endFrame:
                            endFrame = listOfCompletedFrames[i]
                            break
                if endFrame is None:
                    endFrame = FrameFile(queuedFrame.endFrame)
                    endFrame.loadImageData()

                # Initialise the mid frame with the output path
                midFrame = FrameFile(queuedFrame.middleFrame)

                midFrame = rifeInterpolate(device, model, beginFrame, endFrame, midFrame,
                                           queuedFrame.scenechangeSensitivity)
                listOfCompletedFrames.append(midFrame)
                # outFramesQueue.put(midFrame)
        except Exception as e:
            # Put current frame back into queue for another batch thread to process
            framesQueue.put(currentQueuedFrameList)
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)

            # Kill batch thread
            freeVRAM(model,device)
            print("Freed VRAM from dead thread")
            break

        # Add interpolated frames to png save queue
        outputFramesList:SaveFramesList = SaveFramesList(listOfCompletedFrames,currentQueuedFrameList.startFrameDest,currentQueuedFrameList.endFrameDest)

        '''for midFrame1 in listOfCompletedFrames:
            outFramesQueue.put(midFrame1)'''
        outFramesQueue.put(outputFramesList)

        # Start frame is no-longer needed, remove from RAM
        with inFrameGetLock:
            for i in range(0,len(inFramesList)):
                if str(inFramesList[i]) == currentQueuedFrameList.startFrame:
                    inFramesList.pop(i)
                    break
    print("END")

def freeVRAM(model, device):
    del model
    del device
    gc.collect()
    torch.cuda.empty_cache()

def queueThreadSaveFrame(outFramesQueue: Queue):
    while True:
        item: SaveFramesList = outFramesQueue.get()
        if item is None:
            print("Got none - save thread")
            outFramesQueue.put(None)
            break
        currentSavingPNGRange = [item.startOutputFrame,item.endOutputFrame]
        currentSavingPNGRanges.append(currentSavingPNGRange)

        total, used, free = shutil.disk_usage(os.getcwd()[:os.getcwd().index(os.path.sep) + 1])
        freeSpaceInMB = free / (2**20)
        while freeSpaceInMB < 100:
            print("Running out of space on device")
            time.sleep(5)
            total, used, free = shutil.disk_usage(os.getcwd()[:os.getcwd().index(os.path.sep) + 1])
            freeSpaceInMB = free / (2 ** 20)
        item.saveAllPNGsInList()
        currentSavingPNGRanges.remove(currentSavingPNGRange)

def queueThreadLoadFrame(origFramesFolder:str,inFramesList:list):
    maxListLength = 128
    frameFilesList = os.listdir(origFramesFolder)
    frameFilesList.sort()
    for i in range(0,len(frameFilesList)):
        while len(inFramesList) > maxListLength:
            time.sleep(0.01)
        frameFile = FrameFile(origFramesFolder + '/' + frameFilesList[i])
        frameFile.loadImageData()
        inFramesList.append(frameFile)
    print("LOADED ALL FRAMES - DONE")


def createOutput(inputFile, projectFolder, outputVideo, outputFPS, loopable, mode, crfout, useNvenc):
    '''
    Equivalent to DAINAPP Step 3
    '''
    os.chdir(projectFolder)
    maxLoopLength = 15
    preferredLoopLength = 10
    inputLength = getLength(inputFile)

    inputFFmpeg = ""

    encoderPreset = ['-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-preset', 'veryslow',
                     '-crf', '{}'.format(crfout)]
    ffmpegSelected = FFMPEG4
    if useNvenc:
        encoderPreset = ['-pix_fmt', 'yuv420p', '-c:v', 'h264_nvenc', '-gpu', str(GPUID), '-preset', str(nvencPreset),
                         '-profile', 'high', '-rc', 'vbr', '-b:v', '0', '-cq', str(crfout + 10)]
        ffmpegSelected = GlobalValues().getFFmpegPath()

    if mode == 1:
        inputFFmpeg = ['-r', str(outputFPS), '-i', 'interpolated_frames/%15d.png']
    if mode == 3 or mode == 4:
        # generateTimecodesFile(projectFolder)
        chooseFrames(projectFolder + os.path.sep + "interpolated_frames", outputFPS)
        inputFFmpeg = ['-vsync', '1', '-r', str(outputFPS), '-f', 'concat', '-safe', '0', '-i',
                       'interpolated_frames/framesCFR.txt']

    if loopable == False or (maxLoopLength / float(inputLength) < 2):
        # Don't loop, too long input
        print('Dont loop', maxLoopLength / float(inputLength))

        command = [ffmpegSelected, '-hide_banner', '-stats', '-loglevel', 'error', '-y']
        command = command + inputFFmpeg
        command = command + ['-i', str(inputFile), '-map', '0', '-map', '1:a?', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2']
        command = command + encoderPreset + [str(outputVideo)]

        runAndPrintOutput(command)
    else:
        loopCount = math.ceil(preferredLoopLength / float(inputLength)) - 1
        loopCount = str(loopCount)
        print('Loop', loopCount)

        command = [FFMPEG4, '-y', '-stream_loop', str(loopCount), '-i', str(inputFile), '-vn', 'loop.flac']
        runAndPrintOutput(command)

        audioInput = []
        if os.path.exists('loop.flac'):
            audioInput = ['-i', 'loop.flac', '-map', '0', '-map', '1']
            print("Looped audio exists")

        command = [FFMPEG4, '-hide_banner', '-stats', '-loglevel', 'error', '-y', '-stream_loop', str(loopCount)]
        command = command + inputFFmpeg
        command = command + ['-pix_fmt', 'yuv420p', '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-f', 'yuv4mpegpipe', '-']
        command2 = [ffmpegSelected, '-y', '-i', '-']
        command2 = command2 + audioInput + encoderPreset + [str(outputVideo)]

        pipe1 = subprocess.Popen(command, stdout=subprocess.PIPE)
        output = subprocess.check_output(command2, stdin=pipe1.stdout)
        pipe1.wait()
        if os.path.exists('loop.flac'):
            os.remove('loop.flac')


def generateLoopContinuityFrame(framesFolder):
    files = os.listdir(framesFolder)
    files.sort()

    # Find the distance between the first two and last two frames
    # Use this distance to calculate position for the loop continuity frame
    beginFirst = int(files[0][:-4])
    endFirst = int(files[1][:-4])

    beginLast = int(files[-2][:-4])
    endLast = int(files[-1][:-4])

    averageDistance = int(((endFirst - beginFirst) + (endLast - beginLast)) / 2)

    # Create frame
    shutil.copy(framesFolder + '/' + files[0], framesFolder + '/' + '{:015d}.png'.format(endLast + averageDistance))
    print("Made loop continuity frame:", framesFolder + '/' + '{:015d}.png'.format(endLast + averageDistance))


def removeLoopContinuityFrame(framesFolder):
    files = os.listdir(framesFolder)
    files.sort()
    os.remove(framesFolder + '/' + files[-1])


def generateTimecodesFile(projectFolder):
    '''
    Scan a folder full of PNG frames and generate a timecodes file for FFmpeg
    '''
    os.chdir(projectFolder)
    files = os.listdir("interpolated_frames")
    files.sort()

    # Generate duration for last frame
    beginFirst = int(files[0][:-4])
    endFirst = int(files[1][:-4])

    beginLast = int(files[-2][:-4])
    endLast = int(files[-1][:-4])

    averageDistance = int(((endFirst - beginFirst) + (endLast - beginLast)) / 2)

    f = open("interpolated_frames/frames.txt", "w")
    for i in range(0, len(files) - 1):
        # Calculate time duration between frames
        currentFrameFile = files[i]
        nextFrameFile = files[i + 1]
        # Each file has a .png extention, use [:-4] to remove
        frameDuration = int(int(nextFrameFile[:-4]) - int(currentFrameFile[:-4]))
        # Write line
        f.write(
            "file '" + projectFolder + "/interpolated_frames/" + currentFrameFile + "'\nduration " + "{:.5f}".format(
                float(frameDuration / float(GlobalValues.timebase))) + "\n")

    # Generate last frame
    lastFrameName = "{:015d}.png".format(endLast)
    f.write("file '" + projectFolder + "/interpolated_frames/" + lastFrameName + "'\nduration " + "{:.5f}".format(
        float(averageDistance / float(GlobalValues.timebase))) + "\n")
    f.close()

def getOutputFPS(inputFile: str, mode: int, interpolationFactor: int, useAccurateFPS: bool,
                 accountForDuplicateFrames: bool, mpdecimateSensitivity):

    if (mode == 3 or mode == 4) and accountForDuplicateFrames:
        return (getFrameCount(inputFile, True, mpdecimateSensitivity) / getLength(inputFile)) * interpolationFactor

    if useAccurateFPS:
        return getFPSaccurate(inputFile) * interpolationFactor
    else:
        return getFPS(inputFile) * interpolationFactor

def performAllSteps(inputFile, interpolationFactor, loopable, mode, crf, clearPNGs, nonLocalPNGs,
                    scenechangeSensitivity, mpdecimateSensitivity, useNvenc, useAutoEncode=False,
                    autoEncodeBlockSize=3000, useAccurateFPS=True, accountForDuplicateFrames=False, step1=True,
                    step2=True, step3=True):
    # Get project folder path and make it if it doesn't exist
    projectFolder = inputFile[:inputFile.rindex(os.path.sep)]
    if nonLocalPNGs:
        projectFolder = installPath + os.path.sep + "tempFrames"
        if not os.path.exists(projectFolder):
            os.mkdir(projectFolder)
    if step1:
        # Clear pngs if they exist
        if os.path.exists(projectFolder + '/' + 'original_frames'):
            shutil.rmtree(projectFolder + '/' + 'original_frames')

        if os.path.exists(projectFolder + '/' + 'interpolated_frames'):
            shutil.rmtree(projectFolder + '/' + 'interpolated_frames')

        extractFrames(inputFile, projectFolder, mode, mpdecimateSensitivity)
        if not step2 and not step3:
            return

    # Get outputFPS
    outputFPS = getOutputFPS(inputFile,mode,interpolationFactor,useAccurateFPS,accountForDuplicateFrames,mpdecimateSensitivity)

    # Generate output name
    outputVideoNameSegments = ['{:.2f}'.format(outputFPS), 'fps-', str(interpolationFactor), 'x-mode', str(mode),
                               '-rife-',inputFile[inputFile.rindex(os.path.sep) + 1:inputFile.rindex('.')],'.mp4']
    outputVideoName = inputFile[:inputFile.rindex(os.path.sep) + 1] + ''.join(outputVideoNameSegments)

    if step2:
        #Auto encoding
        interpolationDone = [False]

        autoEncodeThread = None
        if useAutoEncode:
            ''' Wait for the thread to start, because python is stupid, and will not start it
            if the interpolator manages to start first'''
            waitForThreadStart = [False]
            if mode == 1:
                autoEncodeThread = threading.Thread(target=autoEncoding.mode1AutoEncoding_Thread,args=(waitForThreadStart, projectFolder,inputFile,outputVideoName,interpolationDone,outputFPS,crf,useNvenc,gpuIDsList[0],currentSavingPNGRanges,autoEncodeBlockSize,))
            elif mode == 3 or mode == 4:
                autoEncodeThread = threading.Thread(target=autoEncoding.mode34AutoEncoding_Thread, args=(waitForThreadStart, projectFolder, inputFile, outputVideoName, interpolationDone, outputFPS, crf, useNvenc,gpuIDsList[0],currentSavingPNGRanges,autoEncodeBlockSize,))
            autoEncodeThread.start()
            while waitForThreadStart[0] == False:
                time.sleep(1)


        outParams = runInterpolator(inputFile, projectFolder, interpolationFactor, loopable, mode,
                                    scenechangeSensitivity, outputFPS)
        print('---INTERPOLATION DONE---')
        interpolationDone[0] = True
        if useAutoEncode:
            autoEncodeThread.join()
            print("---AUTO ENCODING DONE---")

    if step3:
        if not useAutoEncode:
            createOutput(inputFile, projectFolder, outputVideoName, outputFPS, loopable, mode, crf, useNvenc)

        if clearPNGs:
            shutil.rmtree(projectFolder + '/' + 'original_frames')
            shutil.rmtree(projectFolder + '/' + 'interpolated_frames')


def batchInterpolateFolder(inputDirectory, mode, crf, fpsTarget, clearpngs, nonlocalpngs, scenechangeSensitivity,
                           mpdecimateSensitivity, useNvenc, useAccurateFPS=True, accountForDuplicateFrames=True,
                           useAutoEncode=False, autoEncodeBlockSize=3000):
    files = []
    # r=root, d=directories, f = files
    for r, d, f in os.walk(inputDirectory):
        for file in f:
            files.append(os.path.join(r, file))

    files.sort()

    for inputVideoFile in files:
        try:
            print(inputVideoFile)

            currentFPS = getOutputFPS(inputVideoFile,mode,1,useAccurateFPS,accountForDuplicateFrames,mpdecimateSensitivity)

            # Attempt to interpolate everything to above 59fps
            targetFPS = fpsTarget
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
                performAllSteps(inputVideoFile, (2 ** exponent), True, mode, crf, clearpngs, nonlocalpngs,
                                scenechangeSensitivity, mpdecimateSensitivity, useNvenc, useAutoEncode,
                                autoEncodeBlockSize,useAccurateFPS,accountForDuplicateFrames)
            else:
                print("DON'T LOOP")
                performAllSteps(inputVideoFile, (2 ** exponent), False, mode, crf, clearpngs, nonlocalpngs,
                                scenechangeSensitivity, mpdecimateSensitivity, useNvenc, useAutoEncode,
                                autoEncodeBlockSize,useAccurateFPS,accountForDuplicateFrames)
        except:
            traceback.print_exc()
