# Python File startphoenix.py
import sys
from command import *
from configuration import PhoenixConfiguration

if len(sys.argv) != 2:
    printImportant('Usage: python startphoenix.py <path to phoenix configuration file>')
    sys.exit()

phoenix_config = PhoenixConfiguration()
phoenix_config.UploadConfiguration(sys.argv[1])
startPhoenix(phoenix_config)
