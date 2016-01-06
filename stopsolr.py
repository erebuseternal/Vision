# Python File stopsolr.py
from configuration import *
from command import *
import sys

if len(sys.argv) != 3:
    print '\033[93m to use startsolr.py please specify two arguments in this order:'
    print ' path to system configuration file'
    print ' path to keeper configuration file'
    print ' Thanks!! :D \033[0m'
    sys.exit()

# first we must load in our configurations
system_config = SystemConfiguration()
system_config.UploadConfiguration(sys.argv[1])
keeper_config = KeeperConfiguration()
keeper_config.UploadConfiguration(sys.argv[2])

printImportant('Stopping SolrNodes')
stopSolrNodes(system_config)
printImportant('Stopping Keepers')
stopKeepers(system_config, keeper_config)
