# Python File typehandler.py

"""
We are going to need ways to translate between phoenix types
and solr types. And it would be much better if our schema can
be written in terms of solr and then we have machinery that
does the translating to phoenix for us. This is what I hope to
write herein.
"""

"""
First thing we are going to want is an enum that contains
the various types we expect to use in Solr. This will be
the language spoken by our type handler code.
"""

# BOOL
def bool_to_tinyint(value):
    truths = [1, 't', 'T', '1']
    if value in truths:
        return 1
    else:
        return 0

def tinyint_to_bool(value):
    truths = ['1', 1]
    if value in truths:
        return 1
    else:
        return 0

# DATERANGE
def daterange_to_date(value):
    date = value[:10] # cutting off T at end of date in solr value
    time = value[11:-1] # cutting off Z at end of solr value
    new_value = date + ' ' + time
    return new_value

def date_to_daterange(value):
    date = value[:10]
    time = value[11:]   # through these two steps we cut out the space between
                        # date and time
    new_value = date + 'T' + time + 'Z'
    return new_value



# Keepvalue
def keep_value(value):
    return value

# Text
def text_to_varchar_array(value):
    # this is just going to take our text and turn it into 255 character chunks
    # and return the chunks as a list
    length = len(value)
    start = 0
    end = 0
    array = []
    for i in range(255, length, 255):
        end = i
        array.append(value[start:end])
        start = end
    # now we just grab the last chunk
    array.append(value[start:])
    return array

def varchar_array_to_text(value):
    # just take an array of strings and put them together
    new_value = ''
    for string in value:
        new_value = new_value + string
    return new_value

"""
The following enum works like so:
names are solr type names and values are the corresponding phoenix
type. Then, there are two methods that can be called to return the
function to translate either forwards or backwards between the solr
and phoenix types attached to the Enum
"""

class Type:

    # this is how I'm forcing this to work like an Enum is supposed to
    def __getattr__(self, attr):
        self.name = attr
        if attr == 'Bool':
            self.value = 'TINYINT'
        if attr == 'DateRange':
            self.value = 'DATE'
        if attr == 'Str':
            self.value = 'VARCHAR'
        if attr == 'Text':
            self.value = 'VARCHAR ARRAY'
        if attr == 'TrieDouble':
            self.value = 'DOUBLE'
        if attr == 'TrieInt':
            self.value = 'INTEGER'
        if attr == 'TrieLong':
            self.value = 'BIGINT'
        if attr == 'TrieFloat':
            self.value = 'FLOAT'
        return self # this is so that I can go t=Type() t.Text and get something

    def __eq__(self, other):
        if self.name == other.name:
            return True
        else:
            return False

    def __repr__(self):
        if self.name:
            return 'Type: ' + self.name
        else:
            return 'Type: None'


    def __init__(self):
        self.forward_translators = {}
        self.backward_translators = {}
        # now we set the translators :)
        self.forward_translators['Bool'] = bool_to_tinyint
        self.backward_translators['Bool'] = tinyint_to_bool
        self.forward_translators['DateRange'] = daterange_to_date
        self.backward_translators['DateRange'] = date_to_daterange
        self.forward_translators['Text'] = text_to_varchar_array
        self.backward_translators['Text'] = varchar_array_to_text

    def PhoenixType(self):
        return self.value

    def SolrType(self):
        return self.name

    # forwards means from solr to phoenix, backwards is of course the opposite
    def ForwardTranslator(self):
        if self.name in self.forward_translators:
            return self.forward_translators[self.name]
        else:
            return keep_value

    def BackwardTranslator(self):
        if self.name in self.backward_translators:
            return self.backward_translators[self.name]
        else:
            return keep_value

def getTypeEnum(string):
    # so this is going to take a string name, and convert it to
    # the enum
    if string == 'Bool':
        return Type().Bool
    elif string == 'DateRange':
        return Type().DateRange
    elif string == 'Str':
        return Type().Str
    elif string == 'Text':
        return Type().Text
    elif string == 'TrieDouble':
        return Type().TrieDouble
    elif string == 'TrieInt':
        return Type().TrieInt
    elif string == 'TrieLong':
        return Type().TrieLong
    elif string == 'TrieFloat':
        return Type().TrieFloat

"""
Next we are going to have some code here to read in schema files and help turn them
into CREATE TABLE statements!!!
"""

from xmlextractor import XMLExtractor
import re

class SolrSchemaIngestor:
    """
    This class takes a solr schema and first extracts the schema,
    and then processes it for easy use.
    """

    def __init__(self, directory=''):
        self.extractor = XMLExtractor(directory)
        self.fieldTypeExpression = re.compile('"?solr.([^ ]*)Field"?') # used for
                        # finding the group that holds the type name

    def InputFile(self, file_name):
        self.extractor.InputFile(file_name)

    def CreateDocument(self):
        # we will both extract the document here and set it to be the class'
        # document
        self.extractor.CreateDocument()
        self.document = self.extractor.document

    def Process(self):
        """
        Okay so this is going to do a couple things:
        1. It's going to determine the fieldTypes, namely it will create a
        dictionary fieldTypes that will contain the name given to each type
        and then the actual data type enum as a value
        2. It's going to determine the fields, namely it will create a
        dictionary fields that will contain the name of the field and then
        the data type enum corresponding. Note because the fieldType names are
        what let us know the data type for the fields we have to do #1 first
        3. Discover the key

        We will just call three functions to do these things
        """
        self.DiscoverFieldTypes()
        self.DiscoverFields()
        self.DiscoverKey()

    def DiscoverFieldTypes(self):
        """
        This is going to run through the nodes in self.document
        and its going to find all the field types and record the
        name as a key of a dictionary and the type enum as the value
        """
        # we do this by calling an recursive function
        self.fieldTypes = {}
        for node in self.document.nodes:
            self.grabFieldTypes(node)

    def grabFieldTypes(self, node):
        # this looks to see if it is a fieldType, then we assign key value
        # pair to self.fieldTypes with the key being the name and the value
        # being the type enum. If it isn't a fieldType we look at its children
        # if it has any
        if node.name == 'fieldType':
            type_string = self.getTypeName(node.attributes['class'])
            type_enum = getTypeEnum(type_string)
            self.fieldTypes[node.attributes['name'][1:-1]] = type_enum
            # we get rid of the quotes on the attribute with the [1:-1]
        else:
            for child in node.children:
                self.grabFieldTypes(child)

    def getTypeName(self, class_attr):
        # uses a regular expression to catch the name from a string like
        # solr.TextField or "solr.TextField"
        match = re.search(self.fieldTypeExpression, class_attr)
        return match.group(1) # return the group holding the name we are looking for

    """
    Now that we can discover the field types we want to be able to link the
    actual fields to their types (this will be useful in creating tables with
    Phoenix). So assuming the fieldTypes dictionary has been filled we call
    the next function to grab field names and the corresponding types
    """
    def DiscoverFields(self):
        # same as discover types in how this works
        # the dictionary we end up with is field names as keys and the type enum
        # as the value
        self.fields = {}
        for node in self.document.nodes:
            self.grabFields(node)

    def grabFields(self, node):
        # this looks to see if it is a field. If it is it grabs its name and
        # then, using the type attribute and the fieldTypes dictionary that
        # has already been established, it gets the type too. And puts these
        # two things as key and value in our fields dictionary
        if node.name == 'field':
            # first we get the name
            name = node.attributes['name'][1:-1]    # get rid of quotes too
            # next we get the type
            type_name = node.attributes['type'][1:-1]
            # next get the corresponding type enum from this name
            type_enum = self.fieldTypes[type_name]
            # and now we store key and value
            self.fields[name] = type_enum
        else:
            for child in node.children:
                self.grabFields(child)

    """
    Finally we need to know the unique key (if there is one)
    """

    def DiscoverKey(self):
        # we will use the same approach as the other discover functions
        self.key = None
        for node in self.document.nodes:
            self.grabKey(node)

    def grabKey(self, node):
        # same idea as the other grab methods
        if node.name == 'uniqueKey':
            self.key = node.content.strip()
        else:
            for child in node.children:
                self.grabKey(child)
