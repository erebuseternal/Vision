# Python File command_from_config.py

"""
This file will hold all the ingredients for using configuration objects to
start, stop, and modify keepers and solr
"""

import os

def printImportant(string):
    string = '\033[93m' + string + '\033[0m'
    print(string)

class Hadoop:
    def __init__(self, hadoop_dir):
        self.hadoop_dir = hadoop_dir

    def Start(self):
        command1 = '%s/sbin/start-dfs.sh' % self.hadoop_dir
        command2 = '%s/sbin/start-yarn.sh' % self.hadoop_dir
        printImportant('Using commands to start:')
        printImportant(command1)
        os.system(command1)
        printImportant(command2)
        os.system(command2)

    def Stop(self):
        command1 = '%s/sbin/stop-yarn.sh' % self.hadoop_dir
        command2 = '%s/sbin/stop-dfs.sh' % self.hadoop_dir
        printImportant('Using commands to start:')
        printImportant(command1)
        os.system(command1)
        printImportant(command2)
        os.system(command2)

class HBase:
    def __init__(self, hbase_dir):
        self.hbase_dir = hbase_dir

    def Start(self):
        command = '%s/bin/start-hbase.sh' % self.hbase_dir
        printImportant('Starting with command: %s' % command)
        os.system(command)

    def Stop(self):
        command = '%s/bin/stop-hbase.sh' % self.hbase_dir
        printImportant('Stopping with command: %s' % command)
        os.system(command)

class Phoenix:
    def __init__(self, ph_dir):
        self.ph_dir = ph_dir

    def Start(self):
        command = '%s/bin/queryserver.py' % self.ph_dir
        printImportant('Starting query server with command: %s' % command)
        os.system(command)

def startPhoenix(phoenix_config):
    # this starts hadoop, hbase, and then the phoenix query server
    # given a phoenix configuration object
    hadoop_dir = phoenix_config.properties['Hadoop'][0]
    hbase_dir = phoenix_config.properties['HBase'][0]
    phoenix_dir = phoenix_config.properties['Phoenix'][0]
    hadoop = Hadoop(hadoop_dir)
    hbase = HBase(hbase_dir)
    phoenix = Phoenix(phoenix_dir)
    hadoop.Start()
    hbase.Start()
    phoenix.Start()

class Zookeeper:
    # this class will hold all we want for acting upon, starting, and stopping
    # a zookeeper from python

    def __init__(self, configuration_file, zookeeper_dir):
        self.config = configuration_file
        self.zk_dir = zookeeper_dir

    def Start(self):
        # here we just start up the zookeeper with its config
        command = '%s/bin/zkServer.sh start %s' % (self.zk_dir, self.config)
        printImportant('Starting with: %s' % command)
        os.system(command)

    def Stop(self):
        # and here we stop the zookeeper
        command = '%s/bin/zkServer.sh stop %s' % (self.zk_dir, self.config)
        printImportant('Stopping with: %s' % command)
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
