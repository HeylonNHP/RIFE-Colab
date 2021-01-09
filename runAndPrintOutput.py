import subprocess
def runAndPrintOutput(arrayCommand:list):
    result = subprocess.run(arrayCommand, shell=True, text=True, stderr=subprocess.STDOUT, check=False).stdout
    print(result)
