import os
import sys
import time
import globals
import ssh_utils


def validate_installation():
    exit_status, stdout = ssh_utils.run_cmd("express --help")
    print("exit_status={}".format(exit_status))
    print("stdout={}".format(stdout))
