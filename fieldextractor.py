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
