from QueuedFrames.FrameFile import FrameFile


class SaveFramesList:
    framesList:list = None
    startOutputFrame:str = None
    endOutputFrame:str = None
    def __init__(self, framesList,startOutputFrame,endOutputFrame):
        self.framesList = framesList
        self.startOutputFrame = startOutputFrame
        self.endOutputFrame = endOutputFrame

    def saveAllPNGsInList(self):
        for item in self.framesList:
            frameFile:FrameFile = item
            frameFile.saveImageData()