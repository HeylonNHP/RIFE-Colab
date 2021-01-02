import os

def chooseFrames(framesFolder, desiredFPS):
    frameFiles = os.listdir(framesFolder)
    frameFiles.sort()
    lastFile = int(frameFiles[-1][:-4])
    desiredFrameSpacing = (1/desiredFPS)*1000
    timecodesFileString = ""
    currentTime = desiredFrameSpacing
    count = 1
    currentListIndex = 0
    while (currentTime-desiredFrameSpacing) <= lastFile:
        currentFrame = int(frameFiles[currentListIndex][:-4])

        while not (currentFrame >= round(currentTime-desiredFrameSpacing) ): #and currentFrame <= round(currentTime)):
            if not currentListIndex >= len(frameFiles)-1:
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
        currentTime = ((1/desiredFPS)*count)*1000
    print(timecodesFileString)
    outFile = open(framesFolder + os.path.sep + 'framesCFR.txt','w')
    outFile.write(timecodesFileString)
    outFile.close()