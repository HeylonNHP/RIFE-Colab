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

        ffmpegCommand = ['ffmpeg','-loglevel','quiet','-vsync','1','-r',str(outputFPS),'-f', 'concat', '-safe', '0', '-i', blockFramesFilePath]
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
    p2 = run(['ffmpeg','-f','concat','-safe','0','-i',concatFilePath,'-i',inputFile,'-map','0','-map','1:a?','-c','copy', outputFile])
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
        for i in range(0, blockSize):
            filesInBlock.append(interpolatedFrames[i])

        # Keep duration of each block to use for maintaining correct timing when concatenating all blocks
        chosenFrames, blockDuration = chooseFramesList(filesInBlock,outputFPS)
        blockDurations.append(blockDuration)

        framesFileString = ""
        for file in chosenFrames:
            line = "file '" + interpolatedFramesFolder + os.path.sep + file + "'\n"
            framesFileString += line

        blockFramesFilePath = projectFolder + os.path.sep + 'blockFrames{}.txt'.format(blockCount)
        blockFramesFile = open(blockFramesFilePath, 'w')
        blockFramesFile.write(framesFileString)
        blockFramesFile.close()

        encodingPreset = []
        if useNvenc:
            encodingPreset = ['-pix_fmt', 'yuv420p', '-c:v', 'h264_nvenc', '-gpu','0','-preset','slow','-profile','high','-rc', 'vbr', '-b:v', '0', '-cq',str(crfout+10)]
        else:
            encodingPreset = ['-pix_fmt', 'yuv420p', '-c:v', 'libx264', '-preset', 'veryslow', '-crf', '{}'.format(crfout)]

        ffmpegCommand = ['ffmpeg','-loglevel','quiet','-vsync','1','-r',str(outputFPS),'-f', 'concat', '-safe', '0', '-i', blockFramesFilePath]
        ffmpegCommand = ffmpegCommand + encodingPreset
        ffmpegCommand = ffmpegCommand + [projectFolder + os.path.sep + 'autoblock' + str(blockCount) + '.mkv']

        p1 = run(ffmpegCommand)
        #p1.wait()
        blockCount += 1
        #Remove auto-encoded frames
        for file in filesInBlock:
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
    p2 = run(['ffmpeg','-f','concat','-safe','0','-i',concatFilePath,'-i',inputFile,'-map','0','-map','1:a?','-c','copy', outputFile])
    #p2.wait()
    for i in range(1,blockCount):
        os.remove(projectFolder + os.path.sep + 'autoblock' + str(i) + '.mkv')
    os.remove(concatFilePath)