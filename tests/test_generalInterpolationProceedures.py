from generalInterpolationProceedures import extractFrames
def test_extract_frames():
    inputFolder = r'D:\Videos\test'
    inputFile = r'D:\Videos\test\2020-08-10 18.38.30.mov'
    mode = 3
    extractFrames(inputFile,inputFolder,mode)
    mode = 1
    extractFrames(inputFile, inputFolder, mode)
    assert True
