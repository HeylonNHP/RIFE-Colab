import subprocess
def runAndPrintOutput(arrayCommand:list):
    result = subprocess.run(arrayCommand, shell=False, universal_newlines=True, stderr=subprocess.STDOUT, check=False).stdout
    print(result)
