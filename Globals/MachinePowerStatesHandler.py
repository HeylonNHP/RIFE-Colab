import os

import runAndPrintOutput
class MachinePowerStatesHandler:
    def shutdownComputer(self):
        if os.name == 'nt':
            runAndPrintOutput.runAndPrintOutput(['shutdown','/s','/t','1'])
        else:
            # Ubuntu
            runAndPrintOutput.runAndPrintOutput(['systemctl','poweroff'])

    def suspendComputer(self):
        if os.name == 'nt':
            runAndPrintOutput.runAndPrintOutput(['rundll32','Powrprof.dll,SetSuspendState','Sleep'])
        else:
            # Ubuntu
            runAndPrintOutput.runAndPrintOutput(['systemctl','suspend'])