class EncoderConfig:
    nvencGPUID = 0
    useNvenc = False
    useH265 = False
    encodingPreset = "veryslow"
    encodingProfile = "high"
    encodingCRF = 20
    pixelFormat = "yuv420p"

    availableProfilex264 = ['baseline','main','high','high444p']
    availableProfilex265 = ['main','main10']
    availableEncodingPresetsx26x = ['ultrafast','superfast','veryfast','faster','fast','medium','slow','slower','veryslow','placebo']
    availableEncodingPresetsNvenc = ['fast','medium','slow','lossless']
    crfRange = [0,51]

    enableFFmpegOutputFPS = False
    FFmpegOutputFPS = 60

    # Looping
    preferredLoopLength = 10
    maxLoopLength = 15
    # Enable looping the output
    loopRepetitionsEnabled = True

    def __init__(self):
        pass

    def setLoopingOptions(self,preferredLength:float, maxLength:float, loopingEnabled:bool):
        self.preferredLoopLength = preferredLength
        self.maxLoopLength = maxLength
        self.loopRepetitionsEnabled = loopingEnabled

    def getLoopingOptions(self):
        return [self.preferredLoopLength,self.maxLoopLength,self.loopRepetitionsEnabled]

    def setNvencGPUID(self,gpuid:int):
        if not gpuid < 0:
            self.nvencGPUID = gpuid
        else:
            raise Exception("GPU ID out of range")

    def enableNvenc(self,enable:bool):
        self.useNvenc = enable

    def enableH265(self,enable:bool):
        self.useH265 = enable

    def setEncodingPreset(self,preset:str):
        if self.useNvenc:
            if preset not in self.availableEncodingPresetsNvenc:
                raise Exception("Preset doesn't exist")
        else:
            if preset not in self.availableEncodingPresetsx26x:
                raise Exception("Preset doesn't exist")
        self.encodingPreset = preset

    def setEncodingProfile(self,profile:str):
        if self.useH265:
            if not profile in self.availableProfilex265:
                raise Exception("Profile doesn't exist")
        else:
            if not profile in self.availableProfilex264:
                raise Exception("Profile doesn't exist")
        self.encodingProfile = profile

    def setEncodingCRF(self,crf:float):
        if crf > self.crfRange[1] or crf < self.crfRange[0]:
            raise Exception("CRF out of range")
        self.encodingCRF = crf

    def setPixelFormat(self,pixelFormat:str):
        self.pixelFormat = pixelFormat

    def setFFmpegOutputFPS(self,enable:bool,value:float):
        self.enableFFmpegOutputFPS = enable
        self.FFmpegOutputFPS = value


    def getNvencGPUID(self):
        return self.nvencGPUID
    def nvencEnabled(self):
        return self.useNvenc
    def h265Enabled(self):
        return self.useH265
    def getEncodingPreset(self):
        return self.encodingPreset
    def getEncodingProfile(self):
        return self.encodingProfile
    def getEncodingCRF(self):
        return self.encodingCRF
    def getPixelFormat(self):
        return self.pixelFormat
    def getEncoder(self):
        if self.useNvenc:
            if not self.useH265:
                return 'h264_nvenc'
            else:
                return 'hevc_nvenc'
        else:
            if not self.useH265:
                return 'libx264'
            else:
                return 'libx265'

    def FFmpegOutputFPSEnabled(self):
        return self.enableFFmpegOutputFPS
    def FFmpegOutputFPSValue(self):
        return self.FFmpegOutputFPS
