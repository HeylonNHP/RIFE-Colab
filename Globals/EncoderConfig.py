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
    _availableEncodingPresetsx26x = ['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower',
                                     'veryslow', 'placebo']
    _availableEncodingPresetsNvenc = ['fast', 'medium', 'slow', 'lossless']
    _crfRange = [0, 51]

    _enableFFmpegOutputFPS = False
    _FFmpegOutputFPS = 60
    _lossless = False

    # Looping
    _preferredLoopLength = 10
    _maxLoopLength = 15
    # Enable looping the output
    loopRepetitionsEnabled = True

    def __init__(self):
        pass

    def set_looping_options(self, preferred_length: float, max_length: float, looping_enabled: bool):
        self._preferredLoopLength = preferred_length
        self._maxLoopLength = max_length
        self.loopRepetitionsEnabled = looping_enabled

    def get_looping_options(self):
        return [self._preferredLoopLength, self._maxLoopLength, self.loopRepetitionsEnabled]

    def set_nvenc_gpu_id(self, gpu_id: int):
        if not gpu_id < 0:
            self._nvencGPUID = gpu_id
        else:
            raise Exception("GPU ID out of range")

    def enable_nvenc(self, enable: bool):
        self._useNvenc = enable

    def enable_h265(self, enable: bool):
        self._useH265 = enable

    def set_encoding_preset(self, preset: str):
        if self._useNvenc:
            if preset not in self._availableEncodingPresetsNvenc:
                raise Exception("Preset doesn't exist")
        else:
            if preset not in self._availableEncodingPresetsx26x:
                raise Exception("Preset doesn't exist")
        self._encodingPreset = preset

    def set_encoding_profile(self, profile: str):
        if self._useH265:
            if profile not in self._availableProfilex265:
                raise Exception("Profile doesn't exist")
        else:
            if profile not in self._availableProfilex264:
                raise Exception("Profile doesn't exist")
        self._encodingProfile = profile

    def set_encoding_crf(self, crf: float):
        if crf > self._crfRange[1] or crf < self._crfRange[0]:
            raise Exception("CRF out of range")
        self._encodingCRF = crf

    def set_pixel_format(self, pixel_format: str):
        self._pixelFormat = pixel_format

    def set_ffmpeg_output_fps(self, enable: bool, value: float):
        self._enableFFmpegOutputFPS = enable
        self._FFmpegOutputFPS = value

    def get_nvenc_gpu_id(self):
        return self._nvencGPUID

    def nvenc_enabled(self):
        return self._useNvenc

    def h265_enabled(self):
        return self._useH265

    def get_encoding_preset(self):
        if self._lossless and self._useNvenc:
            return "lossless"
        return self._encodingPreset

    def get_encoding_profile(self):
        return self._encodingProfile

    def get_encoding_crf(self):
        if self._lossless:
            return 0
        return self._encodingCRF

    def get_pixel_format(self):
        return self._pixelFormat

    def get_encoder(self):
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

    def ffmpeg_output_fps_enabled(self):
        return self._enableFFmpegOutputFPS

    def ffmpeg_output_fps_value(self):
        return self._FFmpegOutputFPS

    def set_lossless_encoding(self, enable: bool):
        self._lossless = enable
