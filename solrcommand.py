# Python File command_from_config.py

"""
This file will hold all the ingredients for using configuration objects to
start, stop, and modify keepers and solr
"""

import os

class Zookeeper:
    # this class will hold all we want for acting upon, starting, and stopping
    # a zookeeper from python

    def __init__(self, configuration_file, zookeeper_dir):
        self.config = configuration_file
        self.zk_dir = zookeeper_dir

    def Start(self):
        # here we just start up the zookeeper with its config
        command = '%s/bin/zkServer.sh start %s' % (self.zk_dir, self.config)
        print('Starting with: %s' % command)
        os.system(command)

    def Stop(self):
        # and here we stop the zookeeper
        command = '%s/bin/zkServer.sh stop %s' % (self.zk_dir, self.config)
        print('Stopping with: %s' % command)
        os.system(command)


class CommandException(Exception):
    def __init__(self, problem):
        self.problem = problem
    def __str__(self):
        return 'ERROR: command failed because of the problem: %s' % self.problem

def startKeepers(system_config, keeper_config):
    # this will start keepers using the configuration objects input
    # first a simple check to make sure our properties are not None
    for key in system_config.properties:
        if not system_config.properties[key]:
            raise CommandException('%s in system configuration has value None' % key)
    for key in keeper_config.properties:
        if not keeper_config.properties[key]:
            raise CommandException('%s in keeper configuration has value None' % key)
    # now that we know that that simple problem is out of the way, we are going to
    # go on blind faith... :P
    zookeeper_dir = system_config.properties['Zookeeper']
    keeper_configs = keeper_config.properties['Zookeeper']
    # we have to run through the stuff for each zookeeper we added in the config
    for config in keeper_configs:
        keeper = Zookeeper(config, zookeeper_dir)   # create a zookeeper handler object
        keeper.Start()

def stopKeepers(system_config, keeper_config):
    # this will start keepers using the configuration objects input
    # first a simple check to make sure our properties are not None
    for key in system_config.properties:
        if not system_config.properties[key]:
            raise CommandException('%s in system configuration has value None' % key)
    for key in keeper_config.properties:
        if not keeper_config.properties[key]:
            raise CommandException('%s in keeper configuration has value None' % key)
    # now that we know that that simple problem is out of the way, we are going to
    # go on blind faith... :P
    zookeeper_dir = system_config.properties['Zookeeper']
    keeper_configs = keeper_config.properties['Zookeeper']
    # we have to run through the stuff for each zookeeper we added in the config
    for config in keeper_configs:
        keeper = Zookeeper(config, zookeeper_dir) # create a zookeeper handler object
        keeper.Stop()
