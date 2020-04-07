import os
import sys
import time
import globals
import ssh_utils
import user_io
import subprocess


def validate_installation():
    exit_status, stdout = ssh_utils.run_cmd("express --version")
    if exit_status == 0:
        return(True)
    return(False)


def init(url, username, password, tenant, region):
    sys.stdout.write("\n[Initialize Express-CLI]\n")
    if not validate_installation():
        sys.stdout.write("ERROR: missing pip package: express-cli\n")
        return(False)
    if not build_config(url, username, password, tenant, region):
        sys.stdout.write("ERROR: failed to build express-cli config file\n")
        return(False)

    return(True)


def build_config(url, username, password, tenant, region):
    sys.stdout.write("--> Building configuration file for Express-CLI\n")
    
    # validate express base directory exists
    if not os.path.isdir(globals.EXPRESS_BASE_DIR):
        try:
            os.path.mkdir(globals.EXPRESS_BASE_DIR)
        except:
            sys.stdout.write("ERROR: failed to create directory: {}\n".format(globals.EXPRESS_BASE_DIR))
            sys.exit(1)

    # validate express config directory exists
    if not os.path.isdir(globals.EXPRESS_CONFIG_DIR):
        try:
            os.path.mkdir(globals.EXPRESS_CONFIG_DIR)
        except:
            sys.stdout.write("ERROR: failed to create directory: {}\n".format(globals.EXPRESS_CONFIG_DIR))
            sys.exit(1)

    cmd = "express config create --du_url {} --os_username {} --os_password '{}' --os_region {} --os_tenant {}".format(
        url, username, password, region, tenant
    )
    exit_status, stdout = ssh_utils.run_cmd(cmd)
    if exit_status != 0:
        for l in stdout:
            sys.stdout.write(l)
        return(False)

    return(True)


def activate_config(url):
    sys.stdout.write("--> Activating configuration file: {}\n".format(url))
    
    cmd = "express config activate {}".format(url)
    exit_status, stdout = ssh_utils.run_cmd(cmd)
    if exit_status != 0:
        for l in stdout:
            sys.stdout.write(l)
        return(False)

    return(True)


def wait_for_job(p):
    cnt = 0
    minute = 1
    while True:
        if cnt == 0:
            sys.stdout.write(".")
        elif (cnt % 9) == 0:
            sys.stdout.write("|")
            if (minute % 6) == 0:
                sys.stdout.write("\n")
            cnt = -1
            minute += 1
        else:
            sys.stdout.write(".")
        sys.stdout.flush()
        if p.poll() != None:
            break
        time.sleep(1)
        cnt += 1
    sys.stdout.write("\n")


def tail_log(p):
    last_line = None
    while True:
        current_line = p.stdout.readline()
        if not current_line:
            current_line = p.stderr.readline()
        if sys.version_info[0] == 2:
            sys.stdout.write(current_line)
        else:
            sys.stdout.write(current_line.decode())
        if p.poll() != None:
            if current_line == last_line:
                sys.stdout.write("-------------------------------- Process Complete -------------------------------\n")
                break
        last_line = current_line


def map_true_false(s):
    if int(s) == 1:
        return("True")
    else:
        return("False")

def build_cluster(cluster, nodes, username, ssh_key):
    sys.stdout.write("\n[Invoking Express-CLI (to orchestrate cluster provisioning)]\n")
    user_input = user_io.read_kbd("--> Do you want to tail the log", ['q','y','n'], 'y', True, True)
    if user_input == 'q':
        return()

    # build base command args
    command_args = ['express','cluster','create','-u',username,'-s',ssh_key]
    for node in nodes:
        if node['node_type'] == "master":
            command_args.append("-m")
        else:
            command_args.append("-w")
        command_args.append(node['ip'])

        if node['public_ip'] != "":
            command_args.append("-f")
            command_args.append(node['public_ip'])

    # append cluster args
    command_args.append('--masterVip')
    command_args.append(cluster['master_vip_ipv4'])
    command_args.append('--masterVipIf')
    command_args.append(cluster['master_vip_iface'])
    command_args.append('--metallbIpRange')
    command_args.append(cluster['metallb_cidr'])
    command_args.append('--containersCidr')
    command_args.append(cluster['containers_cidr'])
    command_args.append('--servicesCidr')
    command_args.append(cluster['services_cidr'])
    command_args.append('--privileged')
    command_args.append(map_true_false(cluster['privileged']))
    command_args.append('--appCatalogEnabled')
    command_args.append(map_true_false(cluster['app_catalog_enabled']))
    command_args.append('--allowWorkloadsOnMaster')
    command_args.append(map_true_false(cluster['allow_workloads_on_master']))
    command_args.append(cluster['name'])

    # run command (via subprocess)
    cmd = ""
    for c in command_args:
        cmd = "{} {}".format(cmd,c)
    sys.stdout.write("Running: {}\n".format(cmd))
    c = subprocess.Popen(command_args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    if user_input == 'y':
        sys.stdout.write("----------------------------------- Start Log -----------------------------------\n")
        tail_log(c)
    else:
        wait_for_job(c)

