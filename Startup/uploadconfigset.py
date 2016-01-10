# Python File uploadconfigsets.py
from configuration import *
from command import *
import sys

if len(sys.argv) != 3:
    print '\033[93m to use startsolr.py please specify two arguments in this order:'
    print ' path to system configuration file'
    print ' path to configsets configuration file'
    print ' Thanks!! :D \033[0m'
    sys.exit()

# first we must load in our configurations
system_config = SystemConfiguration()
system_config.UploadConfiguration(sys.argv[1])
configset_config = ConfigsetConfiguration()
configset_config.UploadConfiguration(sys.argv[2])

# next we must start everything up using these configurations
# we start with the zookeepers of course
uploadConfigset(system_config, configset_config)
