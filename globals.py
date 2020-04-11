"""Global Variable Defaults"""
from os.path import expanduser

# working directory
HOME_DIR = "{}".format(expanduser("~"))
INSTALL_DIR = "{}/.packet".format(HOME_DIR)

# initialize config context
ctx = {
    "packet": {},
    "platform9": {}
}

# file for storing unique encryption key
ENCRYPTION_KEY_FILE = "{}/.keyfile".format(INSTALL_DIR)

# configuration file
CONFIG_FILE = "{}/pkt.conf".format(HOME_DIR)

# packet API
API_BASEURL = "https://api.packet.net"

# express-cli
EXPRESS_BASE_DIR = "{}/pf9".format(HOME_DIR)
EXPRESS_CONFIG_DIR = "{}/config".format(EXPRESS_BASE_DIR)

# debug variables
flag_skip_launch = False
flag_stop_after_launch = False
