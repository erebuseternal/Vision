# Python File createcollection.py
import sys
from command import *
from configuration import CollectionConfiguration

if len(sys.argv) != 2:
    printImportant('Usage: python createcollection.py <path to collection configuration file>')
    sys.exit()

collection_config = CollectionConfiguration()
collection_config.UploadConfiguration(sys.argv[1])
createCollection(collection_config)
