# https://raevskymichail.medium.com/python-gui-building-a-simple-application-with-pyqt-and-qt-designer-e9f8cda76246
import sys
#from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import mainGuiUi
import os
import threading

sys.path.insert(0, os.getcwd() + os.path.sep + 'arXiv2020RIFE')
print(sys.path)
from generalInterpolationProceedures import *

class RIFEGUIMAINWINDOW(QMainWindow,mainGuiUi.Ui_MainWindow):
    def __init__(self):
        # This is needed here for variable and method access
        super().__init__()
        self.setupUi(self)  # Initialize a design

        self.browseInputButton.clicked.connect(self.browseInputFile)
        self.runAllStepsButton.clicked.connect(self.runAllInterpolationSteps)

    def browseInputFile(self):
        print("TEST")
        file, _filter = QFileDialog.getOpenFileName(caption="Open video file to interpolate")
        print(str(file))
        self.inputFilePathText.setText(file)

    def runAllInterpolationSteps(self):
        print(1)
        selectedGPUs = str(self.gpuidsSelect.currentText()).split(",")
        print(2)
        selectedGPUs = [int(i) for i in selectedGPUs]
        setNvencSettings(selectedGPUs[0], 'slow')
        setGPUinterpolationOptions(int(self.batchthreadsNumber.value()), selectedGPUs)
        print("READING GUI")
        inputFile = str(self.inputFilePathText.text())
        inputFile = inputFile.replace('/','\\')
        print(inputFile)
        interpolationFactor = int(self.interpolationFactorSelect.currentText())
        loopable = bool(self.loopoutputCheck.isChecked())
        mode = int(self.modeSelect.currentText())
        crfout = int(self.crfoutNumber.value())
        clearpngs = bool(self.clearpngsCheck.isChecked())
        nonlocalpngs = bool(self.nonlocalpngsCheck.isChecked())
        scenechangeSensitivity = float(self.scenechangeSensitivityNumber.value())
        mpdecimateSensitivity = str(self.mpdecimateText.text())
        usenvenc = bool(self.nvencCheck.isChecked())
        useAutoencode = bool(self.autoencodeCheck.isChecked())
        blocksize = int(self.autoencodeBlocksizeNumber.value())
        print("FINISHED READING")

        interpolateThread = threading.Thread(target=performAllSteps,args=(inputFile, interpolationFactor, loopable, mode, crfout, clearpngs, nonlocalpngs,
                        scenechangeSensitivity, mpdecimateSensitivity, usenvenc, useAutoencode, blocksize,))

        interpolateThread.start()
        '''performAllSteps(inputFile, interpolationFactor, loopable, mode, crfout, clearpngs, nonlocalpngs,
                        scenechangeSensitivity, mpdecimateSensitivity, usenvenc, useAutoencode, blocksize)'''

def main():
    app = QApplication(sys.argv)
    window = RIFEGUIMAINWINDOW()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()