from frameChooser import chooseFramesList
from runAndPrintOutput import *
import os
import time
import threading


def mode1AutoEncoding_Thread(threadStart:list,projectFolder, inputFile,outputFile, interpolationDone,outputFPS,
                             crfout,useNvenc,blockSize=1000):
    '''

    :param projectFolder: Interpolation project folder
    :param interpolationDone: First index is interpolation state, second index is output fps
    :param blockSize: Size of chunk to autoencode
    :return:
    '''
    print("PROJECT FOLDER", projectFolder)
    interpolatedFramesFolder = projectFolder + os.path.sep + 'interpolated_frames'
    blockFramesFilePath = projectFolder + os.path.sep + 'blockFrames.txt'
    blockCount = 1
    while True:
        threadStart[0] = True
        if not os.path.exists(interpolatedFramesFolder):
            time.sleep(1)
            continue
        interpolatedFrames = os.listdir(interpolatedFramesFolder)
        # Add 128 to wait for the save queue to finish
        if len(interpolatedFrames) < blockSize+(128*8):
            if interpolationDone[0] == False:
                time.sleep(1)
                continue
            else:
                blockSize = len(interpolatedFrames)
                if len(interpolatedFrames) == 0:
                    break
        interpolatedFrames.sort()

        filesInBlock = []
        for i in range(0,blockSize):
            filesInBlock.append(interpolatedFrames[i])

        blockFramesFile = open(blockFramesFilePath,'w')

        framesFileString = ""
        for file in filesInBlock:
            line = "file '" + interpolatedFramesFolder + os.path.sep + file + "'\n"
            framesFileString += line

        blockFramesFile.write(framesFileString)
        blockFramesFile.close()

        encodingPreset = []
        if useNvenc:
            encodingPreset = ['-pix_fmt', 'yuv420p', '-c:v', 'h264_nvenc', '-gpu','0','-preset','slow','-profile','high','-rc', 'vbr', '-b:v', '0', '-cq',str(crfout+10)]
        else:
            encodingPreset = ['-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-preset', 'veryslow', '-crf', '{}'.format(crfout)]

        ffmpegCommand = ['ffmpeg','-y','-loglevel','quiet','-vsync','1','-r',str(outputFPS),'-f', 'concat', '-safe', '0', '-i', blockFramesFilePath]
        ffmpegCommand = ffmpegCommand + encodingPreset
        ffmpegCommand = ffmpegCommand + [projectFolder + os.path.sep + 'autoblock' + str(blockCount) + '.mkv']

        p1 = run(ffmpegCommand)
        #p1.wait()
        blockCount += 1
        #Remove auto-encoded frames
        for file in filesInBlock:
            os.remove(interpolatedFramesFolder + os.path.sep + file)
        os.remove(blockFramesFilePath)

    #Interpolation finished, combine blocks
    concatFileLines = ""
    for i in range(1,blockCount):
        line = "file '" + projectFolder + os.path.sep + 'autoblock' + str(i) + '.mkv' + "'\n"
        concatFileLines += line
    concatFilePath = 'autoConcat.txt'
    concatFile = open(concatFilePath,'w')
    concatFile.write(concatFileLines)
    concatFile.close()
    p2 = run(['ffmpeg','-y','-f','concat','-safe','0','-i',concatFilePath,'-i',inputFile,'-map','0','-map','1:a?','-c:v','copy', outputFile])
    #p2.wait()
    for i in range(1,blockCount):
        os.remove(projectFolder + os.path.sep + 'autoblock' + str(i) + '.mkv')
    os.remove(concatFilePath)

def mode34AutoEncoding_Thread(threadStart:list, projectFolder, inputFile,outputFile, interpolationDone,outputFPS,
                             crfout,useNvenc,blockSize=1000):
    print("PROJECT FOLDER", projectFolder)
    interpolatedFramesFolder = projectFolder + os.path.sep + 'interpolated_frames'

    blockCount = 1
    blockDurations = []

    currentTime = 0
    currentCount = 0
    lastFrameFile = None

    totalLength = 0

    while True:
        threadStart[0] = True
        if not os.path.exists(interpolatedFramesFolder):
            time.sleep(1)
            continue

        interpolatedFrames = os.listdir(interpolatedFramesFolder)
        # Add 1024 to wait for the save queue to finish
        if len(interpolatedFrames) < blockSize+(128*8):
            if interpolationDone[0] == False:
                time.sleep(1)
                continue
            else:
                blockSize = len(interpolatedFrames)
                if len(interpolatedFrames) == 0:
                    break

        interpolatedFrames.sort()

        '''Last frame from last block is kept for use by chooseFramesList
        If the only frame left is the frame kept from the last block
        Then we are finished encoding autoencode blocks'''
        if interpolatedFrames[0] == lastFrameFile and len(interpolatedFrames) == 1:
            break

        # Make list of frames in current block
        filesInBlock = []
        for i in range(0, blockSize):
            filesInBlock.append(interpolatedFrames[i])

        # Get the length in ms of the current block, including the next block start time to get the length of the last frame in the current block
        # Used to keep duration of each block to use for maintaining correct timing when concatenating all blocks
        nextBlockStartTime = None
        try:
            nextBlockStartTime = int(interpolatedFrames[blockSize][:-4])
        except:
            # If frame from next block doesn't exist (I.E. this is the last block) generate time from last frame pair in current block
            nextBlockStartTime = int(interpolatedFrames[blockSize-1][:-4]) + (int(interpolatedFrames[blockSize-1][:-4])-int(interpolatedFrames[blockSize-2][:-4]))

        currentLength = nextBlockStartTime-int(filesInBlock[1][:-4])
        totalLength += currentLength
        print('Auto encode block',blockCount,len(filesInBlock), str(nextBlockStartTime-int(filesInBlock[1][:-4]))+'ms',
              "Before",filesInBlock[0],"Start",filesInBlock[1],'End',filesInBlock[-1])

        # Chose frames for use in output (Downsampling to target FPS)
        chosenFrames, blockDuration, currentTime, currentCount = chooseFramesList(filesInBlock,outputFPS,currentTime,currentCount)

        # blockDurations.append(blockDuration)
        blockDurations.append(currentLength)

        # Save concat file containing all the chosen frames
        framesFileString = ""
        for file in chosenFrames:
            line = "file '" + interpolatedFramesFolder + os.path.sep + file + "'\n"
            framesFileString += line

        blockFramesFilePath = projectFolder + os.path.sep + 'blockFrames{}.txt'.format(blockCount)
        blockFramesFile = open(blockFramesFilePath, 'w')
        blockFramesFile.write(framesFileString)
        blockFramesFile.close()

        # Build ffmpeg command and run ffmpeg
        encodingPreset = []
        if useNvenc:
            encodingPreset = ['-pix_fmt', 'yuv420p', '-c:v', 'h264_nvenc', '-gpu','0','-preset','slow','-profile','high','-rc', 'vbr', '-b:v', '0', '-cq',str(crfout+10)]
        else:
            encodingPreset = ['-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-preset', 'veryslow', '-crf', '{}'.format(crfout)]

        ffmpegCommand = ['ffmpeg','-y','-loglevel','quiet','-vsync','1','-r',str(outputFPS),'-f', 'concat', '-safe', '0', '-i', blockFramesFilePath]
        ffmpegCommand = ffmpegCommand + encodingPreset
        ffmpegCommand = ffmpegCommand + [projectFolder + os.path.sep + 'autoblock' + str(blockCount) + '.mkv']

        p1 = run(ffmpegCommand)

        blockCount += 1
        #Remove auto-encoded frames in current block
        lastFrameFile = filesInBlock[-1]
        for file in filesInBlock:
            # Don't delete last frame file in block, as it is used by chooseFramesList in next block
            if file == lastFrameFile:
                print("KEEP THIS FRAME",file)
                continue
            deleteFile = interpolatedFramesFolder + os.path.sep + file
            os.remove(deleteFile)
        os.remove(blockFramesFilePath)

    #Interpolation finished, combine blocks
    concatFileLines = ""
    for i in range(1,blockCount):
        line = "file '" + projectFolder + os.path.sep + 'autoblock' + str(i) + '.mkv' + "'\n"
        line += 'duration ' + str((blockDurations[i-1])/1000.0) + '\n'
        concatFileLines += line
    concatFilePath = projectFolder + os.path.sep + 'autoConcat.txt'
    concatFile = open(concatFilePath,'w')
    concatFile.write(concatFileLines)
    concatFile.close()
    p2 = run(['ffmpeg','-y','-f','concat','-safe','0','-i',concatFilePath,'-i',inputFile,'-map','0','-map','1:a?','-c:v','copy', outputFile])
    #p2.wait()

    totalDuration = 0
    for duration in blockDurations:
        totalDuration += duration

    print(str(totalDuration))
    print('Test length',totalLength)

    # Remove blocks and concat file - Output is already created, don't need these anymore
    for i in range(1,blockCount):
        os.remove(projectFolder + os.path.sep + 'autoblock' + str(i) + '.mkv')
    os.remove(concatFilePath)