##############################################################################################################
## PKT : Toolkit for Packet.net
##############################################################################################################
import os
import sys

# early functions
def fail(m=None):
    sys.stdout.write("ASSERT: {}\n".format(m))
    sys.exit(1)

# validate python version
if not sys.version_info[0] in [2,3]:
    fail("Unsupported Python Version: {}\n".format(sys.version_info[0]))

# configure where to look for modules
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, 'lib')))

# import modules
import globals, urllib3, requests, json, signal, argparse, packet_cloud, interview
from encrypt import Encryption
from packet_cloud import PacketCloud

# disable ssl warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# functions
def _parse_args():
    ap = argparse.ArgumentParser(sys.argv[0], formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--apply", "-a",  help="Apply configuation", required=False, nargs=1)
    ap.add_argument("--show", "-s",  help="show resources", required=False, nargs=1, choices=['plan','os','facility','device'])
    ap.add_argument("--encrypt", "-e",  help="Encrypt a string", required=False, nargs=1)
    ap.add_argument("--decrypt", "-d",  help="Decrypt a string", required=False, nargs=1)
    ap.add_argument("--key", "-k", help="Encryption key for decrytping secure data", required=False, nargs=1)
    return ap.parse_args()


def motd():
    sys.stdout.write("██████╗ ██╗  ██╗████████╗\n")
    sys.stdout.write("██╔══██╗██║ ██╔╝╚══██╔══╝\n")
    sys.stdout.write("██████╔╝█████╔╝    ██║   \n")
    sys.stdout.write("██╔═══╝ ██╔═██╗    ██║   \n")
    sys.stdout.write("██║     ██║  ██╗   ██║   \n")
    sys.stdout.write("╚═╝     ╚═╝  ╚═╝   ╚═╝   \n\n")
    sys.stdout.write("Welcome to PKT!\n")
    sys.stdout.write("Run: 'pkt -h' for usage information\n")


def init_install_dir():
    if not os.path.isdir(globals.INSTALL_DIR):
        try:
            os.mkdir(globals.INSTALL_DIR)
        except:
            fail("failed to create directory: {}".format(globals.INSTALL_DIR))


def read_config():
    if not os.path.isfile(globals.CONFIG_FILE):
        fail("config file missing: {}".format(globals.CONFIG_FILE))

    if sys.version_info[0] == 2:
        import ConfigParser
        app_config = ConfigParser.ConfigParser()
    else:
        import configparser
        app_config = configparser.ConfigParser()

    try:
        app_config.read(globals.CONFIG_FILE)
        return(app_config)
    except Exception as ex:
        fail("ConfigParser.Exception: {}\n".format(ex.message))


def write_config(config_values):
    try:
        config_fh = open(globals.CONFIG_FILE, "w")
        config_fh.write("[packet.net]\n")
        config_fh.write("token = {}\n".format(config_values['api_key']))
        config_fh.write("project_id = {}\n".format(config_values['project_id']))
        config_fh.close()
    except:
        fail("failed to write config file: {}\n".format(globals.CONFIG_FILE))

    # validate config was written
    if not os.path.isfile(globals.CONFIG_FILE):
        fail("failed to write config file: {}\n".format(globals.CONFIG_FILE))


def init_keyfile(encryption_key):
    if os.path.isfile(globals.ENCRYPTION_KEY_FILE):
        try:
            os.remove(globals.ENCRYPTION_KEY_FILE)
        except:
            fail("failed to remove keyfile: {}".format(globals.ENCRYPTION_KEY_FILE))

    # write user-supplied encryption key to keyfile
    try:
        data_file_fh = open(globals.ENCRYPTION_KEY_FILE, "w")
        data_file_fh.write("{}".format(encryption_key))
        data_file_fh.close()
    except:
        fail("failed to initialize keyfile for encryption: {}".format(globals.ENCRYPTION_KEY_FILE))


###########################################################################################
## main
###########################################################################################
def main():
    args = _parse_args()

    # validate installation directory
    init_install_dir()

    # initialize encryption/decryption key (keyfile)
    if args.key:
        init_keyfile(args.key[0])
        sys.exit(0)

    # initialize encryption
    encryption = Encryption(globals.ENCRYPTION_KEY_FILE)

    # encryption functions
    if args.encrypt:
        sys.stdout.write("Encrypted string: {}\n".format(encryption.encrypt_string(args.encrypt[0])))
        sys.exit(0)
    elif args.decrypt:
        sys.stdout.write("Decrypted string: {}\n".format(encryption.decrypt_string(args.decrypt[0])))
        sys.exit(0)

    # prompt user for Packet credentials (if config_file is missing)
    if not os.path.isfile(globals.CONFIG_FILE):
        config_values = interview.get_config()
        if config_values:
            write_config(config_values)

    # read config file
    app_config = read_config()

    # get parameter values from config
    project_id = app_config.get('packet.net','project_id')
    token = encryption.decrypt_string(app_config.get('packet.net','token'))
    if not token:
        fail("failed to decrypt API key")

    # init packet cloud
    packet_cloud = PacketCloud(token, project_id)

    # validate credentials
    valid_creds = packet_cloud.validate_creds()
    if not valid_creds:
        try:
            os.remove(globals.CONFIG_FILE)
        except:
            sys.stdout.write("ERROR: failed to remove config file with invalid credentials: {}\n".format(globals.CONFIG_FILE))
        fail("failed to login into Packet.net with the supplied credentials\n")

    # run function (based on commandline args)
    if args.apply:
        packet_cloud.run_action(args.apply[0])
    elif args.show and args.show[0] == "plan":
        packet_cloud.show_plans()
    elif args.show and args.show[0] == "os":
        packet_cloud.show_operating_systems()
    elif args.show and args.show[0] == "facility":
        packet_cloud.show_facilities()
    elif args.show and args.show[0] == "device":
        packet_cloud.show_devices()
    else:
        motd()

    # exit cleanly
    sys.exit(0)

if __name__ == "__main__":
    main()
