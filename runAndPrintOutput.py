from subprocess import Popen, PIPE, STDOUT, run


def run_and_print_output(array_command: list):
    # result = run(arrayCommand, shell=False, universal_newlines=True, stderr=STDOUT, check=False).stdout
    p = Popen(array_command, shell=False, universal_newlines=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT,
              close_fds=True)
    result = p.stdout.read()
    print(result)
