import subprocess
def runAndPrintOutput(arrayCommand:list):
    result = subprocess.check_output(arrayCommand, shell=True, text=True, stderr=subprocess.STDOUT)
    print(result)
