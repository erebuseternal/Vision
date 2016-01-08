# Python File typehandler.py

"""
We are going to need ways to translate between phoenix types
and solr types. And it would be much better if our schema can
be written in terms of solr and then we have machinery that
does the translating to phoenix for us. This is what I hope to
write herein.
"""

from enum import Enum

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

class Type(Enum):
    Bool = 'TINYINT'
    DateRange = 'DATE'
    Str = 'VARCHAR'
    Text = 'VARCHAR ARRAY'
    TrieDouble = 'DOUBLE'
    TrieInt = 'INTEGER'
    TrieLong = 'BIGINT'
    TrieFloat = 'FLOAT'

    def __init__(self):
        Enum.__init__(self)
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

"""
Next we are going to have some code here to read in schema files and turn them
into CREATE TABLE statements!!!
"""
