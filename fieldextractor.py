# Python File fieldextractor.py

"""
This will allow us to read in a structured document. Find the nodes
with the name field, and then copy them over another class which
allows you to access them by name as if from a dictionary.
"""

import copy
from xmlextractor import XMLExtractor

class FieldExtractor:
    """
    This takes in an xml document and pulls out the fields
    """

    def __init__(self, directory=''):
        self.fields = {}
        self.directory = directory
        self.xml_extractor = XMLExtractor(directory)

    def InputFile(self, address):
        self.xml_extractor.InputFile(address)

    def ExtractFields(self):
        self.fields = {}
        self.xml_extractor.CreateDocument()
        structured_doc = self.xml_extractor.document
        for node in structured_doc.nodes:
            self.extract(node)

    def extract(self, node):
        # this will add the node
        if node.name == 'field':
            self.fields[node.attributes['name'][1:-1]] = self.processNode(node) # we have to cut off the quotations on the attribute
        for child in node.children:
            self.extract(child)

    def processNode(self, node):
        # this just creates a modified node so it is a standalone without children
        new_node = copy.deepcopy(node)
        new_node.parent = None
        new_node.older_sibling = None
        new_node.younger_sibling = None
        new_node.children = None
        return new_node

    def __getitem__(self, key):
        # so that we can access the field node content off of this object like accessing a dictionary
        return self.fields[key].content

"""
The next function will go ahead and take a document (with solr syntax), extract
it, extract the fields and then return those fields as a FieldExtractor
"""

import re

class FieldTracker:
    """
    This class takes an html file and then looks for the name
    tag and then each of the |{fieldname} instances

    Name tag is like <tableName value="table_name" />
    """
    def __init__(self, directory=''):
        self.found_tag = False
        self.field_markers = []
        self.directory = directory
        self.xml_extractor = XMLExtractor(directory)
        self.expression = re.compile('\|\{([^\{\} ]*)\}')
        self.text = ''

    def InputFile(self, address):
        self.xml_extractor.InputFile(address)
        self.file = address

    def Process(self):
        # first we get the table name
        self.getTableName()
        self.findFieldMarkers()

    def getTableName(self):
        self.xml_extractor.CreateDocument()
        for node in self.xml_extractor.document.nodes:
            self.findNameTag(node)
            if self.found_tag == True:
                break

    def findNameTag(self, node):
        if not self.found_tag:
            if node.name == 'tableName':
                self.table_name = node.attributes['value'][1:-1]
                self.found_tag = True
            for child in node.children:
                if self.found_tag == True:
                    break
                self.findNameTag(child)

    def findFieldMarkers(self):
        # first we read the file
        text = open(self.file, 'r').read()
        self.text = text
        prior = []
        # next we look for matches for fieldmarkers
        for match in re.finditer(self.expression, text):
            # next we make sure the pipe isn't escaped by looking at the char before
            if text[match.start() - 1] == '\\':
                continue
            # alright, so we know it isn't escaped, so we record it
            to_append = (match.start(), match.end(), match.group(1)) # the index of the start of the match, the end, and the field name
            prior.append(to_append)
        # now we are going to loop through the list backwards so we can construct it
        # forwards to front so when we go through replacing markers with values we just
        # work right through the list from front to back without worrying about changing indices we need
        # to keep track of
        for i in range(-1, -len(prior) - 1, -1):
            print i
            self.field_markers.append(prior[i])

"""
The following function takes a FieldMarker (that has processed everything) and a FieldExtractor (which has processed
things) and returns the newly made HTML
"""

def joinData(field_dictionary, field_tracker):
    # so we just loop through the field markers and make our replacements as we go
    text = field_tracker.text
    for tup in field_tracker.field_markers:
        start = tup[0]
        end = tup[1]
        field = tup[2]
        value = field_dictionary[field] # just needs to act like a dictionary
                                        # a field extractor works just fine here
        text = text[0:start] + value + text[end:] # yes you would think it would be
                # end + 1, but just end works :/ guessing match.end() returns
                # the 'end' of the substring such that text[start:end] returns the
                # match
    return text
