# Python File startsolr.py
from configuration import *
from command import *
import sys

if len(sys.argv) != 4:
    print '\033[93m to use startsolr.py please specify three arguments in this order:'
    print ' path to system configuration file'
    print ' path to keeper configuration file'
    print ' path to solr configuration file'
    print ' Thanks!! :D \033[0m'
    sys.exit()

# first we must load in our configurations
system_config = SystemConfiguration()
system_config.UploadConfiguration(sys.argv[1])
keeper_config = KeeperConfiguration()
keeper_config.UploadConfiguration(sys.argv[2])
solr_config = SolrConfiguration()
solr_config.UploadConfiguration(sys.argv[3])

# next we must start everything up using these configurations
# we start with the zookeepers of course
printImportant('Starting keepers')
startKeepers(system_config, keeper_config)
printImportant('Starting solr nodes')
startSolrNodes(system_config, solr_config)
