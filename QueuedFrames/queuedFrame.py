class QueuedFrame:
    beginFrame:str = None
    endFrame:str = None
    middleFrame:str = None
    scenechangeSensitivity = None
    def __init__(self, beginFrame, endFrame, middleFrame, scenechangeSensitivity):
        self.beginFrame = beginFrame
        self.endFrame = endFrame
        self.middleFrame = middleFrame
        self.scenechangeSensitivity = scenechangeSensitivity
