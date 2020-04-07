import os
import sys
import requests
import json
import globals
import reports
import time
from encrypt import Encryption


class PacketCloud:
    """Interact with Packet Cloud"""
    def __init__(self, token, project_id):
        self.token = token
        self.project_id = project_id


    def validate_creds(self):
        try:
            api_endpoint = "/projects/{}/plans".format(self.project_id)
            headers = { 'content-type': 'application/json', 'X-Auth-Token': self.token }
            rest_response = requests.get("{}/{}".format(globals.API_BASEURL,api_endpoint), verify=False, headers=headers)
            if rest_response.status_code == 200:
                return(True)
        except:
            return(False)

        return(False)


    def wait_for_instances(self, instance_uuids):
        booted_instances = []
        start_time = int(time.time())
        TIMEOUT = 5
        POLL_INTERVAL = 15
        timeout = int(time.time()) + (60 * TIMEOUT)
        flag_all_active = False
        while True:
            # loop over all instances and get status
            for tmp_uuid in instance_uuids:
                instance_status = self.get_instance_status(tmp_uuid)
                if instance_status == "active":
                    if not tmp_uuid in booted_instances:
                        booted_instances.append(tmp_uuid)
                time.sleep(1)

            # check if all instances have become active
            tmp_flag = True
            for tmp_uuid in instance_uuids:
                if not tmp_uuid in booted_instances:
                    tmp_flag = False
                    break

            if tmp_flag:
                flag_all_active = True
                break
            elif int(time.time()) > timeout:
                break
            else:
                time.sleep(POLL_INTERVAL)

        # enforce TIMEOUT
        if not flag_all_active:
            return(False,0)

        # calculate time to launch all instances
        end_time = int(time.time())
        time_elapsed = end_time - start_time

        return(True,time_elapsed)
        

    def launch_instance(self, hostname, action):
        post_payload = {
            'batches': [
                {
                    'hostname': hostname,
                    'facility': action['facility'],
                    'plan': action['plan'],
                    'operating_system': action['operating_system'],
                    'userdata': action['userdata'],
                    'customdata': action['customdata'],
                    'quantity': 1,
                    'ip_addresses': action['ip_addresses']
                }
            ]
        }

        # perform post operation
        try:
            api_endpoint = "projects/{}/devices/batch".format(self.project_id)
            headers = { 'content-type': 'application/json', 'X-Auth-Token': self.token }
            rest_response = requests.post("{}/{}".format(globals.API_BASEURL,api_endpoint), verify=False, headers=headers, data=json.dumps(post_payload))
            if rest_response.status_code != 201:
                return(None, rest_response.text)
        except Exception as ex:
            sys.stdout.write("ERROR: failed to launch instance ({})\n".format(ex.message))
            return(None, ex.message)

        # parse rest response
        try:
            json_response = json.loads(rest_response.text)
            time.sleep(10)
            instance_uuid = self.get_device_uuid(hostname)
            return(instance_uuid, None)
        except:
            sys.stdout.write("INFO: failed to launch instance (failed to retrieve the batch id)\n")
            return(None, "failed to retrieve the batch id")


    def launch_batch_instances(self, action):
        sys.stdout.write("ACTION = {}\n\n".format(action['operation']))

        # valid action JSON
        required_keys = ['num_instances','plan']
        for key_name in required_keys:
            if not key_name in action:
                sys.stdout.write("ERROR: missing required key in action: {}".format(key_name))
                return(None)

        # prepare to launch instances
        table_title = "------ Action Parameters ------"
        table_columns = ["Plan","Data Center","Operating System","Hostname Base","# Instances"]
        table_rows = [ 
            [action['plan'], action['facility'], action['operating_system'], action['hostname_base'], action['num_instances']]
        ]
        reports.display_table(table_title, table_columns, table_rows)
        
        # launch instances
        sys.stdout.write("\n[Launching Instances]\n")
        instance_uuids = []
        LAUNCH_INTERVAL = 5
        cnt = 1
        while cnt <= action['num_instances']:
            target_hostname = "{}{}".format(action['hostname_base'], str(cnt).zfill(2))

            # validate host does not exists | TODO: update to allow for duplicate hostnames
            instance_uuid = self.get_device_uuid(target_hostname)
            if instance_uuid and (not globals.flag_skip_launch):
                sys.stdout.write("FATAL: existing host with identical name found in inventory\n")
                sys.exit(0)

            if globals.flag_skip_launch:
                sys.stdout.write("--> skipping (globals.flag_skip_launch = {})\n".format(globals.flag_skip_launch))
            else:
                sys.stdout.write("--> launching {}\n".format(target_hostname))
                instance_uuid, launch_message = self.launch_instance(target_hostname, action)
                if not instance_uuid:
                    sys.stdout.write("ERROR: failed to launch instance ({})\n".format(launch_message))
                    return(None)
                time.sleep(LAUNCH_INTERVAL)

            instance_uuids.append(instance_uuid)
            cnt += 1

        return(instance_uuids)


    def run_action(self, spec_file):
        if not os.path.isfile(spec_file):
            sys.stdout.write("ERROR: failed to open spec file: {}".format(spec_file))
            return(None)

        with open(spec_file) as json_file:
            spec_actions = json.load(json_file)

        required_keys = ['actions']
        for key_name in required_keys:
            if not key_name in spec_actions:
                sys.stdout.write("ERROR: missing required key in spec file: {}".format(key_name))
                return(None)

        # loop over actions (run sequentially/synchronously)
        for action in spec_actions['actions']:
            if 'operation' not in action:
                sys.stdout.write("ERROR: invalid json syntax, missing: operation\n")
                continue

            # invoke action-specific functions
            if action['operation'] == "launch-instance":
                required_keys = ['num_instances','hostname_base','plan','facility','operating_system','userdata','customdata','ip_addresses']
                for key_name in required_keys:
                    if not key_name in action:
                        sys.stdout.write("ERROR: missing required key in spec file: {}".format(key_name))
                        return(None)

                instance_uuids = self.launch_batch_instances(action)
                if instance_uuids:
                    sys.stdout.write("\n[Waiting for All Instances to Boot]\n")
                    all_instances_booted, boot_time = self.wait_for_instances(instance_uuids)
                    if all_instances_booted:
                        sys.stdout.write("--> all instances booted successfully, boot time = {} seconds\n\n".format(boot_time))
                        self.show_devices(instance_uuids)
                    else:
                        sys.stdout.write("--> TIMEOUT exceeded\n")
            elif action['operation'] == "pf9-build-cluster":
                required_keys = ['pmk_region','cluster','ssh_username','ssh_key']
                for key_name in required_keys:
                    if not key_name in action:
                        sys.stdout.write("ERROR: missing required key in spec file: {}".format(key_name))
                        return(None)

                # initialize encryption
                encryption = Encryption(globals.ENCRYPTION_KEY_FILE)

                # initialize/login in Platform9 PMK
                sys.stdout.write("\n[Initializing PMK Integration]\n")
                from pf9_pmk import PMK
                pf9 = PMK(
                    action['pmk_region']['url'],
                    action['pmk_region']['username'],
                    encryption.decrypt_string(action['pmk_region']['password']),
                    action['pmk_region']['tenant']
                )

                # validate login to Platform9
                if not pf9.validate_login():
                    sys.stdout.write("ERROR: failed to login to PMK region: {} (user={}/{}, tenant={})\n".format(du_url,du_user,du_password,du_tenant))
                    return(None)
                else:
                    sys.stdout.write("--> logged into PMK region: {} (user={}/tenant{})\n".format(
                        action['pmk_region']['url'],action['pmk_region']['username'],action['pmk_region']['tenant'])
                    )

                # build node_list
                node_list = [
                    {
                      'ip': '139.178.89.141',
                      'public_ip': '',
                      'node_type': 'master'
                    }
                ]

                # build Kubernetes cluster on PMK
                pf9.onboard_cluster(
                    action['pmk_region']['url'],
                    action['pmk_region']['username'],
                    encryption.decrypt_string(action['pmk_region']['password']),
                    action['pmk_region']['tenant'],
                    action['pmk_region']['region'],
                    action['cluster'],
                    node_list,
                    action['ssh_username'],
                    action['ssh_key']
                )

    def get_plans(self):
        try:
            api_endpoint = "/projects/{}/plans".format(self.project_id)
            headers = { 'content-type': 'application/json', 'X-Auth-Token': self.token }
            rest_response = requests.get("{}/{}".format(globals.API_BASEURL,api_endpoint), verify=False, headers=headers)
            if rest_response.status_code == 200:
                try:
                    json_response = json.loads(rest_response.text)
                    return(json_response)
                except:
                    return(None)
        except:
            return(None)

        return(None)


    def show_plans(self):
        # query packet API
        plans = self.get_plans()

        # initialize table for report
        from prettytable import PrettyTable
        tmp_table = PrettyTable()
        tmp_table.title = "Plans"
        tmp_table.field_names = ["Name","Class","Price","Memory","CPU","NIC","Storage"]
        tmp_table.align["Name"] = "l"
        tmp_table.align["Class"] = "l"
        tmp_table.align["Price"] = "l"
        tmp_table.align["Memory"] = "l"
        tmp_table.align["CPU"] = "l"
        tmp_table.align["NIC"] = "l"
        tmp_table.align["Storage"] = "l"

        for plan in plans['plans']:
            plan_memory = "-"
            plan_nic = "-"
            plan_disk = "-"
            plan_cpu = "-"
            for s in plan['specs']:
                if s == 'memory':
                    plan_memory = plan['specs'][s]['total']
                if s == 'cpus':
                    num_cpu = 0
                    cpu_type = "-"
                    for cpu in plan['specs'][s]:
                        cpu_type = plan['specs'][s][num_cpu]['type']
                        num_cpu += 1
                    plan_cpu = "({}) {}".format(num_cpu, cpu_type)
                if s == 'nics':
                    num_nic = 0
                    nic_type = "-"
                    for nic in plan['specs'][s]:
                        nic_type = plan['specs'][s][num_nic]['type']
                        num_nic += 1
                    plan_nic = "({}) {}".format(num_nic, nic_type)
                if s == 'drives':
                    num_disk = 0
                    disk_type = "-"
                    for disk in plan['specs'][s]:
                        disk_type = plan['specs'][s][num_disk]['type']
                        num_disk += 1
                    plan_disk = "({}) {}".format(num_disk, disk_type)
            plan_name = plan['name']
            plan_class = plan['class']
            plan_price = plan['pricing']['hour']
            tmp_table.add_row([plan_name,plan_class,plan_price,plan_memory,plan_cpu,plan_nic,plan_disk])

        sys.stdout.write("------ {} ------\n".format(tmp_table.title))
        print(tmp_table)

    def get_oses(self):
        try:
            api_endpoint = "/operating-systems"
            headers = { 'content-type': 'application/json', 'X-Auth-Token': self.token }
            rest_response = requests.get("{}/{}".format(globals.API_BASEURL,api_endpoint), verify=False, headers=headers)
            if rest_response.status_code == 200:
                try:
                    json_response = json.loads(rest_response.text)
                    return(json_response)
                except:
                    return(None)
        except:
            return(None)

        return(None)


    def show_operating_systems(self):
        # query packet API
        oses = self.get_oses()

        # initialize table for report
        from prettytable import PrettyTable
        tmp_table = PrettyTable()
        tmp_table.title = "Operating Systems"
        tmp_table.field_names = ["Name","Distro","Version","Preinstallable","Licensed"]
        for tmp_field in tmp_table.field_names:
            tmp_table.align[tmp_field] = "l"

        for os in oses['operating_systems']:
            tmp_table.add_row([os['name'],os['distro'],os['version'],os['preinstallable'],os['licensed']])

        sys.stdout.write("------ {} ------\n".format(tmp_table.title))
        print(tmp_table)


    def get_facilities(self):
        try:
            api_endpoint = "/facilities"
            headers = { 'content-type': 'application/json', 'X-Auth-Token': self.token }
            rest_response = requests.get("{}/{}".format(globals.API_BASEURL,api_endpoint), verify=False, headers=headers)
            if rest_response.status_code == 200:
                try:
                    json_response = json.loads(rest_response.text)
                    return(json_response)
                except:
                    return(None)
        except:
            return(None)

        return(None)


    def show_facilities(self):
        # query packet API
        facilities = self.get_facilities()

        # initialize table for report
        from prettytable import PrettyTable
        tmp_table = PrettyTable()
        tmp_table.title = "Data Centers"
        tmp_table.field_names = ["Name","Code","UUID"]
        for tmp_field in tmp_table.field_names:
            tmp_table.align[tmp_field] = "l"

        for os in facilities['facilities']:
            tmp_table.add_row([os['name'],os['code'],os['id']])

        sys.stdout.write("------ {} ------\n".format(tmp_table.title))
        print(tmp_table)


    def get_devices(self):
        try:
            api_endpoint = "/projects/{}/devices".format(self.project_id)
            headers = { 'content-type': 'application/json', 'X-Auth-Token': self.token }
            rest_response = requests.get("{}/{}".format(globals.API_BASEURL,api_endpoint), verify=False, headers=headers)
            if rest_response.status_code == 200:
                try:
                    json_response = json.loads(rest_response.text)
                    return(json_response)
                except:
                    return(None)
        except:
            return(None)

        return(None)


    def show_devices(self, filter_uuid_list=None):
        # query packet API
        devices = self.get_devices()

        # initialize table for report
        from prettytable import PrettyTable
        tmp_table = PrettyTable()
        tmp_table.title = "Devices"
        tmp_table.field_names = ["Facility","Hostname","State","Operating System","Volumes","Storage","IP Addresses","Created"]
        for tmp_field in tmp_table.field_names:
            tmp_table.align[tmp_field] = "l"

        for d in devices['devices']:
            if filter_uuid_list and (not d['id'] in filter_uuid_list):
                continue

            facility_name = "{} (uuid={})".format(d['facility']['name'],d['facility']['code'])
            creation_info = "{}\n{}".format(d['created_at'],d['id'])
            ip_addrs = None
            for i in d['ip_addresses']:
                if ip_addrs:
                    ip_addrs = "{}\n{}".format(ip_addrs,i['address'])
                else:
                    ip_addrs = "{}".format(i['address'])
              
            tmp_table.add_row([facility_name,d['hostname'],d['state'],d['operating_system']['name'],d['volumes'],d['storage'],ip_addrs,creation_info])

        sys.stdout.write("------ {} ------\n".format(tmp_table.title))
        print(tmp_table)


    def get_device_uuid(self, hostname):
        # query packet API
        devices = self.get_devices()
        for d in devices['devices']:
            if d['hostname'] == hostname:
                return(d['id'])

        return(None)


    def get_instance_status(self, instance_uuid):
        instance_state = "inactive"
        try:
            api_endpoint = "/devices/{}".format(instance_uuid)
            headers = { 'content-type': 'application/json', 'X-Auth-Token': self.token }
            rest_response = requests.get("{}/{}".format(globals.API_BASEURL,api_endpoint), verify=False, headers=headers)
            if rest_response.status_code == 200:
                try:
                    json_response = json.loads(rest_response.text)
                    return(json_response['state'])
                except:
                    return(instance_state)
        except Exception as ex:
            return(instance_state)

        return(instance_state)
