import sys
import os
import globals
import user_io
from encrypt import Encryption


def get_config():
    config_values = {
    }

    # get Packet credentials
    sys.stdout.write("\nPlease enter credentials for Packet.Net:\n")
    project_id = user_io.read_kbd("--> Project ID", [], '', True, True)
    if project_id == "q":
        return ''

    api_key = user_io.read_kbd("--> API Key", [], '', False, True)
    if api_key == "q":
        return ''

    # get Platform9 credentials
    sys.stdout.write("\nPlease enter credentials for Platform9.Com:\n")
    pmk_region_url = user_io.read_kbd("--> PMK Region URL", [], '', True, True)
    if pmk_region_url == "q":
        return ''

    pmk_username = user_io.read_kbd("--> Username", [], '', True, True)
    if pmk_username == "q":
        return ''

    pmk_password = user_io.read_kbd("--> Password", [], '', False, True)
    if pmk_password == "q":
        return ''

    pmk_tenant = user_io.read_kbd("--> Tenant", [], 'service', True, True)
    if pmk_tenant == "q":
        return ''

    pmk_region = user_io.read_kbd("--> Region Name", [], 'RegionOne', True, True)
    if pmk_region == "q":
        return ''

    # initialize encryption
    encryption = Encryption(globals.ENCRYPTION_KEY_FILE)

    # update config (encrypt api_key)
    config_values['project_id'] = project_id
    config_values['api_key'] = encryption.encrypt_string(api_key)
    config_values['pmk_region_url'] = pmk_region_url
    config_values['pmk_username'] = pmk_username
    config_values['pmk_password'] = encryption.encrypt_string(pmk_password)
    config_values['pmk_tenant'] = pmk_tenant
    config_values['pmk_region'] = pmk_region

    sys.stdout.write("\n")
    return(config_values)

