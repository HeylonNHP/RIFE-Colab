import os

import runAndPrintOutput
class MachinePowerStatesHandler:
    def shutdownComputer(self):
        if os.name == 'nt':
            runAndPrintOutput.run_and_print_output(['shutdown', '/s', '/t', '1'])
        else:
            # Ubuntu
            runAndPrintOutput.run_and_print_output(['systemctl', 'poweroff'])

    def suspendComputer(self):
        if os.name == 'nt':
            runAndPrintOutput.run_and_print_output(['rundll32', 'Powrprof.dll,SetSuspendState', 'Sleep'])
        else:
            # Ubuntu
            runAndPrintOutput.run_and_print_output(['systemctl', 'suspend'])