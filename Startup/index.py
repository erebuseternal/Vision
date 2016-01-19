#Python File index.py

"""
This is just a shortcut for me so I can index documents in solr really easily.
"""

import os
import sys
from command import *
from configuration import IndexConfiguration

def formatString(string):
    # replaces spaces with %20's
    words = string.split(' ')
    final_string = words[0]
    for i in range(1, len(words)):
        final_string = final_string + '%20' + words[i]
    return final_string

if len(sys.argv) != 2:
    printImportant('Usage: pythonindex.py <path to index configuration file>')
    sys.exit()

index_config = IndexConfiguration()
index_config.UploadConfiguration(sys.argv[1])
solr_address = index_config.properties['SolrAddress'][0]
data_directory = index_config.properties['DataDirectory'][0]
collection = index_config.properties['Collection'][0]

command_preface = 'curl http://%s/solr/%s/update -H "Content-Type: text/xml" --data-binary @' % (solr_address, collection)
directory = data_directory
for filename in os.listdir(directory):
    filename = formatString(filename)
    printImportant('using command: %s' % (command_preface + directory + '/' + filename))
    os.system(command_preface + directory + '/' + filename)
# now we commit
printImportant('using command: %s' % (command_preface[:-1] + "'<commit waitSearcher=\"false\" />'"))
os.system(command_preface[:-1] + "'<commit waitSearcher=\"false\" />'")
