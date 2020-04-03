"""Global Variable Defaults"""
from os.path import expanduser

# working directory
HOME_DIR = "{}".format(expanduser("~"))
INSTALL_DIR = "{}/.packet".format(HOME_DIR)

# file for storing unique encryption key
ENCRYPTION_KEY_FILE = "{}/.keyfile".format(INSTALL_DIR)

# configuration file
CONFIG_FILE = "{}/k8s_deploy.conf".format(HOME_DIR)

# packet API
API_BASEURL = "https://api.packet.net"
