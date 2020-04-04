import sys
import os
import globals
import user_io
from encrypt import Encryption


def get_config():
    config_values = {
    }

    sys.stdout.write("\nPlease enter credentials for Packet.Net\n")
    project_id = user_io.read_kbd("--> Project ID", [], '', True, True)
    if project_id == "q":
        return ''

    api_key = user_io.read_kbd("--> API Key", [], '', False, True)
    if api_key == "q":
        return ''

    # initialize encryption
    encryption = Encryption(globals.ENCRYPTION_KEY_FILE)

    # update config (encrypt api_key)
    config_values['project_id'] = project_id
    config_values['api_key'] = encryption.encrypt_string(api_key)

    sys.stdout.write("\n")
    return(config_values)

