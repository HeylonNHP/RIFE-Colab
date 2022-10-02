class EncoderConfig:
    _nvencGPUID = 0
    _useNvenc = False
    _useH265 = False
    _encodingPreset = "veryslow"
    _encodingProfile = "high"
    _encodingCRF = 20
    _pixelFormat = "yuv420p"

    _availableProfilex264 = ['baseline', 'main', 'high', 'high444p']
    _availableProfilex265 = ['main', 'main10']
    _availableEncodingPresetsx26x = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow', 'placebo']
    _availableEncodingPresetsNvenc = ['fast', 'medium', 'slow', 'lossless']
    _crfRange = [0, 51]

    _enableFFmpegOutputFPS = False
    _FFmpegOutputFPS = 60

    # Looping
    _preferredLoopLength = 10
    _maxLoopLength = 15
    # Enable looping the output
    loopRepetitionsEnabled = True

    def __init__(self):
        pass

    def setLoopingOptions(self,preferredLength:float, maxLength:float, loopingEnabled:bool):
        self._preferredLoopLength = preferredLength
        self._maxLoopLength = maxLength
        self.loopRepetitionsEnabled = loopingEnabled

    def getLoopingOptions(self):
        return [self._preferredLoopLength, self._maxLoopLength, self.loopRepetitionsEnabled]

    def setNvencGPUID(self,gpuid:int):
        if not gpuid < 0:
            self._nvencGPUID = gpuid
        else:
            raise Exception("GPU ID out of range")

    def enableNvenc(self,enable:bool):
        self._useNvenc = enable

    def enableH265(self,enable:bool):
        self._useH265 = enable

    def setEncodingPreset(self,preset:str):
        if self._useNvenc:
            if preset not in self._availableEncodingPresetsNvenc:
                raise Exception("Preset doesn't exist")
        else:
            if preset not in self._availableEncodingPresetsx26x:
                raise Exception("Preset doesn't exist")
        self._encodingPreset = preset

    def setEncodingProfile(self,profile:str):
        if self._useH265:
            if not profile in self._availableProfilex265:
                raise Exception("Profile doesn't exist")
        else:
            if not profile in self._availableProfilex264:
                raise Exception("Profile doesn't exist")
        self._encodingProfile = profile

    def setEncodingCRF(self,crf:float):
        if crf > self._crfRange[1] or crf < self._crfRange[0]:
            raise Exception("CRF out of range")
        self._encodingCRF = crf

    def setPixelFormat(self,pixelFormat:str):
        self._pixelFormat = pixelFormat

    def setFFmpegOutputFPS(self,enable:bool,value:float):
        self._enableFFmpegOutputFPS = enable
        self._FFmpegOutputFPS = value


    def getNvencGPUID(self):
        return self._nvencGPUID
    def nvencEnabled(self):
        return self._useNvenc
    def h265Enabled(self):
        return self._useH265
    def getEncodingPreset(self):
        return self._encodingPreset
    def getEncodingProfile(self):
        return self._encodingProfile
    def getEncodingCRF(self):
        return self._encodingCRF
    def getPixelFormat(self):
        return self._pixelFormat
    def getEncoder(self):
        if self._useNvenc:
            if not self._useH265:
                return 'h264_nvenc'
            else:
                return 'hevc_nvenc'
        else:
            if not self._useH265:
                return 'libx264'
            else:
                return 'libx265'

    def FFmpegOutputFPSEnabled(self):
        return self._enableFFmpegOutputFPS
    def FFmpegOutputFPSValue(self):
        return self._FFmpegOutputFPS
