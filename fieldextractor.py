# Python File fieldextractor.py

"""
This will allow us to read in a structured document. Find the nodes
with the name field, and then copy them over another class which
allows you to access them by name as if from a dictionary.
"""

import copy

class FieldExtractor:
    """
    This takes in a structured document and pulls out the fields
    """

    def __init__(self):
        self.fields = {}

    def ExtractFields(self, structured_doc):
        self.fields = {}
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
        # so that we can access the field nodes off of this object like accessing a dictionary
        return self.fields[key]

"""
The next function will go ahead and take a document (with solr syntax), extract
it, extract the fields and then return those fields as a FieldExtractor
"""
from xmlextractor import XMLExtractor

def extractFields(self, file, directory=''):
    # first we create the xml extractor
    xml_ex = XMLExtractor(directory)
    xml_ex.InputFile(file)
    xml_ex.CreateDocument()
    document = xml_ex.document
    f_ex = FieldExtractor()
    f_ex.ExtractFields(document)
    return f_ex

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

    def InputFile(self, file):
        self.file = file
        self.xml_extractor.InputFile(file)

    def Process(self):
        # first we get the table name
        self.getTableName()
        self.findFieldMarkers()

    def getTableName(self):
        self.xml_extractor.CreateDocument()
        for node in xml_extractor.document.nodes:
            self.findNameTag(node)
            if self.found_tag = True
                break

    def findNameTag(self, node):
        if not self.found_tag:
            if node.name == 'tableName':
                self.table_name = node.attributes['value'][1:-1]
                self.found_tag = True
            for child in node.children:
                if self.found_tag = True:
                    break
                self.findNameTag(child)

    def findFieldMarkers(self):
        # first we read the file
        text = open(self.directory + self.file, 'r').read()
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
        for i in range(-1, -len(prior), -1):
            self.fieldmarkers.append(prior[i])

"""
The following function takes a FieldMarker (that has processed everything) and a FieldExtractor (which has processed
things) and returns the newly made HTML
"""

def joinData(field_extractor, field_marker):
    # so we just loop through the field markers and make our replacements as we go
    text = field_marker.text
    for tup in field_marker.fieldmarkers:
        start = tup[0]
        end = tup[1]
        field = tup[2]
        value = field_extractor[field]
        text = text[0:start] + value + text[end + 1:]
    return text
