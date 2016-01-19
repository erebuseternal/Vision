# Python file configuration.py

"""
Herein will be objects that will use
configuration files in order to startup zookeeper and solr
"""

class ConfigurationException(Exception):
    def __init__(self, problem):
        self.problem = problem
    def __str__(self):
        return 'ERROR: configuration failed because of the problem: %s' % self.problem

class Configuration:
    """
    This object holds all of our system configuration
    """

    def __init__(self):
        self.properties = {}
        self.defaults = {}
        self.Initiate()
        for key in self.properties:
            # set defaults for later comparison
            self.defaults[key] = self.properties[key]

    def Initiate(self):
        # to be overriden by subclasses :)
        # should set the properties dictionary where keys are strings
        # that show up as keys in the config file and values are the
        # default values for the string
        pass

    def UploadConfiguration(self, path_to_config_file):
        # this loads the configuration from a file
        file = open(path_to_config_file, 'r')
        count = 1
        for line in file:

            line = line.strip() # first we remove unnecessary whitespace
                                # next we check to make sure the line isn't a
            if line[0] == '#':  # comment
                count = count + 1
                continue

            index_of_space = line.find(' ')
                                            # now we check for the space
            if not index_of_space == -1:    # seperating a key from a value
                key = line[0:index_of_space]
                index_of_hash = line.find('#')  # now we deal with comments
                if not index_of_hash == -1:
                    # there is a comment so we have to deal with it
                    line = line[0:index_of_hash].strip()    # we get rid of the
                                                            # comment
                value = line[index_of_space + 1:]
                # finally we want to take a value with spaces in it, and turn
                # it into a list
                if not value.find(' ') == -1:
                    value = value.split(' ')
                # now that we have our key and value we are going to check
                # to see that the key is in our properties, and if it is
                # we shall give it the value found. If it isn't we shall
                # pass it by but warn the user
                if key in self.properties:
                    # I am also going to want a property to be able
                    # to show up multiple times. So I am going to put
                    # the value in a list which we will append to every
                    # time. Of course we shall have remove the default
                    # should something new show up
                    current_value = self.properties[key]
                    if current_value == self.defaults[key]:
                        self.properties[key] = [value]  # set up our list
                    else:
                        self.properties[key].append(value)
                else:
                    print 'WARN: unidentified key found at line %s' % count
            else:
                raise ConfigReadException('No key value pair found on line %s' % count)
            count = count + 1

class SystemConfiguration(Configuration):
    def Initiate(self):
        self.properties['Solr'] = None
        self.properties['Zookeeper'] = None

class KeeperConfiguration(Configuration):
    def Initiate(self):
        self.properties['Zookeeper'] = None

class SolrConfiguration(Configuration):
    def Initiate(self):
        self.properties['ZookeeperAddresses'] = None
        self.properties['Solr'] = None

class PhoenixConfiguration(Configuration):
    def Initiate(self):
        self.properties['Hadoop'] = None
        self.properties['HBase'] = None
        self.properties['Phoenix'] = None

class ConfigsetConfiguration(Configuration):
    def Initiate(self):
        self.properties['Zookeeper'] = None
        self.properties['Name'] = None
        self.properties['Directory'] = None

class CollectionConfiguration(Configuration):
    def Initiate(self):
        self.properties['Name'] = None
        self.properties['NumShards'] = 1
        self.properties['ReplicationFactor'] = 1
        self.properties['ConfigName'] = None
        self.properties['SolrAddress'] = None

class IndexConfiguration(Configuration):
    def Initiate(self):
        self.properties['Collection'] = None
        self.properties['DataDirectory'] = None
        self.properties['SolrAddress'] = None
