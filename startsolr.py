# Python File startsolr.py
from configuration import *
import sys

if len(sys.argv) != 3:
    print '\033[93m to use startsolr.py please specify three arguments in this order:'
    print ' path to system configuration file'
    print ' path to keeper configuration file'
    print ' path to solr configuration file'
    print ' Thanks!! :D \033[0m'
    sys.exit()

# first we must load in our configurations
system_config = SystemConfiguration()
system_config.UploadConfiguration(sys.argv[0])
keeper_config = KeeperConfiguration()
keeper_config.UploadConfiguration(sys.arv[1])
solr_config = SolrConfiguration()
solr_config = SolrConfiguration(sys.argv[2])

# next we must start everything up using these configurations
