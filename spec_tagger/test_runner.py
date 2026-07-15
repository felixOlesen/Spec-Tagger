import subprocess
import shlex

class Runner:
    def __init__(self, test_run_command, linked_tags):
        self.test_run_command = test_run_command
        self.linked_tags = linked_tags

    def build_command(self):
        pass

    def run_tests(self):

        res = subprocess.run(self.test_run_command, capture_output=True, text=True)

        if res.returncode != 0:
            raise Exception("command returned non-zero exit code: " + str(res.returncode))
        if res.stderr:
            raise Exception("command returned output to stderr: " + res.stderr)
        else:
            print(res.stdout)