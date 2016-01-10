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
        command = '%s/bin/queryserver.py start' % self.ph_dir
        printImportant('Starting query server with command: %s' % command)
        os.system(command)

    def Stop(self):
        command = '%s/bin/queryserver.py stop' % self.ph_dir
        printImportant('Stopping query server with command: %s' % command)
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

def stopPhoenix(phoenix_config):
    # this starts hadoop, hbase, and then the phoenix query server
    # given a phoenix configuration object
    hadoop_dir = phoenix_config.properties['Hadoop'][0]
    hbase_dir = phoenix_config.properties['HBase'][0]
    phoenix_dir = phoenix_config.properties['Phoenix'][0]
    hadoop = Hadoop(hadoop_dir)
    hbase = HBase(hbase_dir)
    phoenix = Phoenix(phoenix_dir)
    phoenix.Stop()
    hbase.Stop()
    hadoop.Stop()

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
    zookeeper_dir = system_config.properties['Zookeeper'][0]
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
    zookeeper_dir = system_config.properties['Zookeeper'][0]
    keeper_configs = keeper_config.properties['Zookeeper']
    # we have to run through the stuff for each zookeeper we added in the config
    for config in keeper_configs:
        keeper = Zookeeper(config, zookeeper_dir) # create a zookeeper handler object
        keeper.Stop()

class SolrNode:
    def __init__(self, solr_dir, port, home, keeper_list):
        self.solr_dir = solr_dir
        self.port = port
        self.home = home
        self.keeper_list = keeper_list

    def Start(self):
        keepers = ''
        for keeper in self.keeper_list:
            keepers = keepers + ',' + keeper
        keepers = keepers[1:]
        command = '%s/bin/solr start -p %s -s %s/%s -z %s' % (self.solr_dir, self.port, self.solr_dir, self.home, keepers)
        printImportant('Starting solr node using: %s' % command)
        os.system(command)

def startSolrNodes(system_config, solr_config):
    # first we get the data from the configuration
    solr_dir = system_config.properties['Solr'][0]
    zookeepers = solr_config.properties['ZookeeperAddresses'][0]
    solr_nodes = solr_config.properties['Solr']
    for node in solr_nodes:
        port = node[0]
        home = node[1]
        solr_node = SolrNode(solr_dir, port, home, zookeepers)
        solr_node.Start()

def stopSolrNodes(system_config):
    # just stop all here
    solr_dir = system_config.properties['Solr'][0]
    command = '%s/bin/solr stop -all' % solr_dir
    printImportant('Stopping with command: %s' % command)
    os.system(command)

class ZookeeperClient:
    def __init__(self, zookeeper_address, solr_dir):
        self.zookeeper_address = zookeeper_address
        self.solr_dir = solr_dir

    def UploadConfigset(self, configset_dir, name):
        command = '%s/server/scripts/cloud-scripts/zkcli.sh -zkhost %s -cmd upconfig -confdir %s -confname %s' % (self.solr_dir, self.zookeeper_address, configset_dir, name)
        printImportant('Uploading configset with command: %s' % command)
        os.system(command)

def uploadConfigset(system_config, configset_config):
    solr_dir = system_config.properties['Solr'][0]
    zookeeper_address = configset_config.properties['Zookeeper'][0]
    zookeeper_client = ZookeeperClient(zookeeper_address, solr_dir)
    configset_dir = configset_config.properties['Directory'][0]
    name = configset_config.properties['Name'][0]
    zookeeper_client.UploadConfigset(configset_dir, name)

class SolrAdmin:
    def __init__(self, solr_address):
        self.solr_address = solr_address

    def CreateCollection(self, name, numshards, replicationfactor, configname):
        # have to escape the ampersands
        command = 'curl http://%s/solr/admin/collections?action=CREATE\&name=%s\&numShards=%s\&replicationFactor=%s\&collection.configName=%s' % (self.solr_address, name, numshards, replicationfactor, configname)
        printImportant('Creating collection with command: %s' % command)
        os.system(command)

def createCollection(collection_config):
    solr_address = collection_config.properties['SolrAddress'][0]
    name = collection_config.properties['Name'][0]
    numshards = collection_config.properties['NumShards'][0]
    replicationfactor = collection_config.properties['ReplicationFactor'][0]
    configname = collection_config.properties['ConfigName'][0]
    solradmin = SolrAdmin(solr_address)
    solradmin.CreateCollection(name, numshards, replicationfactor, configname)
