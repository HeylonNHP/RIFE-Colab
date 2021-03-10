class InterpolatorConfig:
    _interpolationFactor = 2
    _loopable = False
    _mode = 1
    _clearPngs = True
    _nonLocalPngs = True
    _scenechangeSensitivity = 0.20
    _mpdecimateSensitivity = "64*12,64*8,0.33"
    _useAccurateFPS = True
    _accountForDuplicateFrames = False

    def setInterpolationFactor(self,interpolationFactor:int):
        self._interpolationFactor = interpolationFactor

    def getInterpolationFactor(self):
        return self._interpolationFactor

    def setLoopable(self,loopable:bool):
        self._loopable = loopable

    def getLoopable(self):
        return self._loopable

    def setMode(self,mode:int):
        modes = [1,3,4]
        assert mode in modes
        self._mode = mode

    def getMode(self):
        return self._mode

    def setClearPngs(self,clearPngs:bool):
        self._clearPngs = clearPngs

    def getClearPngs(self):
        return self._clearPngs

    def setNonlocalPngs(self,nonlocalpngs:bool):
        self._nonLocalPngs = nonlocalpngs

    def getNonlocalPngs(self):
        return self._nonLocalPngs

    def setScenechangeSensitivity(self,sensitivity:float):
        assert 1 >= sensitivity >= 0
        self._scenechangeSensitivity = sensitivity

    def getScenechangeSensitivity(self):
        return self._scenechangeSensitivity

    def setMpdecimateSensitivity(self,sensitivity:str):
        self._mpdecimateSensitivity = sensitivity

    def getMpdecimateSensitivity(self):
        return self._mpdecimateSensitivity

    def setUseAccurateFPS(self,enable:bool):
        self._useAccurateFPS = enable

    def getUseAccurateFPS(self):
        return self._useAccurateFPS

    def setAccountForDuplicateFrames(self,enable:bool):
        self._accountForDuplicateFrames = enable

    def getAccountForDuplicateFrames(self):
        return self._accountForDuplicateFrames
