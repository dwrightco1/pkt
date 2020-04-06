import os
import sys
import time
import globals
import ssh_utils


def validate_installation():
    exit_status, stdout = ssh_utils.run_cmd("express --version")
    if exit_status == 0:
        return(True)
    return(False)


def build_config(url, username, password, tenant, region):
    sys.stdout.write("--> Building configuration file for Express-CLI\n")
    cmd = "express config create --du_url {} --os_username {} --os_password '{}' --os_region {} --os_tenant {}".format(
        url, username, password, region, tenant
    )
    sys.stdout.write("Running: {}\n".format(cmd))
    exit_status, stdout = ssh_utils.run_cmd(cmd)
    sys.stdout.write("-------- express confif create --------------------------------\n")
    for l in stdout:
        sys.stdout.write(l.strip())
    sys.stdout.write("---------------------------------------------------------------\n")
    if exit_status != 0:
        return(False)

    return(True)

