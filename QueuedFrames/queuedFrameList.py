class QueuedFrameList:
    frameList:list = None
    startFrame:str = None
    endFrame:str = None
    def __init__(self, frameList, startFrame, endFrame):
        self.frameList = frameList
        self.startFrame = startFrame
        self.endFrame = endFrame

