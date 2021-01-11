from subprocess import Popen, PIPE, STDOUT, run
def runAndPrintOutput(arrayCommand:list):
    #result = run(arrayCommand, shell=False, universal_newlines=True, stderr=STDOUT, check=False).stdout
    p = Popen(arrayCommand,shell=False,universal_newlines=True,stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
    result = p.stdout.read()
    print(result)
