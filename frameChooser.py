import os


def chooseFrames(framesFolder, desiredFPS):
    frameFiles = os.listdir(framesFolder)
    frameFiles.sort()
    lastFile = int(frameFiles[-1][:-4])
    desiredFrameSpacing = (1 / desiredFPS) * 1000
    timecodesFileString = ""
    currentTime = desiredFrameSpacing
    count = 1
    currentListIndex = 0
    while (currentTime - desiredFrameSpacing) <= lastFile:
        currentFrame = int(frameFiles[currentListIndex][:-4])

        while not (
                currentFrame >= round(currentTime - desiredFrameSpacing)):  # and currentFrame <= round(currentTime)):
            if not currentListIndex >= len(frameFiles) - 1:
                currentListIndex += 1
            else:
                break

            # print(currentListIndex, 'LI', currentFrame, 'CU', count, 'count')
            # print('sanity Check', currentFrame, '>', (currentTime - desiredFrameSpacing), 'and', currentFrame, '<=', currentTime)
            currentFrame = int(frameFiles[currentListIndex][:-4])

        # print('sanity Check SUCCEEDED', currentFrame, '>', (currentTime - desiredFrameSpacing), 'and', currentFrame, '<=', currentTime)
        # Build timecodes file
        frameFile = framesFolder + os.path.sep + frameFiles[currentListIndex]

        timecodesFileString += ("file '" + frameFile + "'\n")

        count += 1
        currentTime = ((1 / desiredFPS) * count) * 1000
    print(timecodesFileString)
    outFile = open(framesFolder + os.path.sep + 'framesCFR.txt', 'w')
    outFile.write(timecodesFileString)
    outFile.close()


def chooseFramesList(frameFiles, desiredFPS):
    '''testFilePath = 'test.txt'
    testFileString = ""
    try:
        testFile = open(testFilePath,'r')
        testFileString = testFile.read()
        testFile.close()
    except:
        pass

    testFile = open(testFilePath,'w')'''

    chosenFrameList: list = []

    #frameFiles = os.listdir(framesFolder)
    frameFiles.sort()

    lastFileNumber = int(frameFiles[-1][:-4])
    desiredFrameSpacing = (1 / desiredFPS) * 1000

    currentTime = desiredFrameSpacing
    count = 1
    currentListIndex = 0

    #testFileString += 'Video clip: '

    # For when the first frame doesn't start from 0ms
    # Advance current time to the first frame's timecode
    while currentTime < int(frameFiles[0][:-4]):
        count += 1
        currentTime = ((1 / desiredFPS) * count) * 1000

    #testFileString += 'Start time: ' + str(currentTime)

    while (currentTime - desiredFrameSpacing) <= lastFileNumber:
        currentFrame = int(frameFiles[currentListIndex][:-4])
        while currentFrame < round(currentTime - desiredFrameSpacing):
            if currentListIndex < len(frameFiles) - 1:
                currentListIndex += 1
            else:
                break
            currentFrame = int(frameFiles[currentListIndex][:-4])
        frameFile = frameFiles[currentListIndex]
        chosenFrameList.append(frameFile)

        count += 1
        currentTime = ((1 / desiredFPS) * count) * 1000
    #testFileString += ' End time: ' + str(currentTime)
    #testFileString += ' Start frame: ' + chosenFrameList[0] + ' End frame: ' + chosenFrameList[-1]
    #testFileString += ' Duration: ' + str((int(chosenFrameList[-1][:-4]) - int(chosenFrameList[0][:-4])))
    #testFileString += '\n'
    #testFile.write(testFileString)
    #testFile.close()
    return chosenFrameList, (int(chosenFrameList[-1][:-4]) - int(chosenFrameList[0][:-4]))
