# Python File starphoenix.py

"""
This is going to be the spot where we put the code that uses
solr schema files and the like to generate tables and the like
through phoenix for hbase.
"""

"""
So, first off we will be loading a schema file and then turning it into
a series of create table statements. The idea is that each schema file
is going to turn into a single table. Now this works out quite easily for
almost every data type... except for text. There is no BLOB type for phoenix
so storing things bigger than 255 characters gets difficult (especially cause
ARRAY isn't working for me). So what we are going to do instead is create
an additional table per text field in solr. Note that this means that no unique
key can be a text field. <<<<<<<<< Anyways, here goes:
"""
class SchemaException(Exception):
    def __init__(self, problem):
        self.problem = problem
    def __str__(self):
        return 'ERROR: schema to phoenix failed because of the problem: %s' % self.problem

from typehandler import *

def GenerateSchema(schema_file, directory=''):
    # returns a schema_ingestor object
    # first we create a SolrSchemaIngestor of course
    schema_ingestor = SolrSchemaIngestor(directory)
    # next we ingest the file
    schema_ingestor.InputFile(schema_file)
    schema_ingestor.CreateDocument()
    schema_ingestor.Process()
    return schema_ingestor

def GenerateCreateTableStatements(table_name, schema_ingestor):
    # first we get the fields
    fields = schema_ingestor.fields
    # next the key
    schema_key = schema_ingestor.key
    # now we check to make sure the key isn't a text field
    if fields[schema_key] == Type().Text:
        raise SchemaException("schema's key is a text field... this is not allowed. Please change to string")
    # next we divide our fields into text fields and other
    text_fields = {}
    other_fields = {}
    for key in fields:
        if fields[key] == Type().Text:
            text_fields[key] = fields[key]
        else:
            other_fields[key] = fields[key]
    # now we go ahead and make the tables
    # we will make one central table that has the other_fields and the schema_key
    # as key. Then we will make a separate table for each text field where the
    # name of the table is the field name, and we have a unique user id, a position
    # number (which will be used to stitch the text back together after we have broken
    # it up into pieces), and the value (which is a varchar).
    # WE START with the other_fields
    statements = {}
    statement = 'CREATE TABLE ' + table_name + ' ('
    for key in other_fields:
        data_type = other_fields[key].value
        field_name = key
        statement = statement + ' ' + field_name + ' ' + data_type
        if key == schema_key:
            statement = statement + ' PRIMARY KEY,'
        else:
            statement = statement + ','
    # now we will get rid of the last comma and replace it with a )
    statement = statement[:-1] + ')'
    statements['primary'] = statement # we do this so we can tell which one
                                    # to do first later
    # now we move onto the text_fields
    for key in text_fields:
        statements[key] = 'CREATE TABLE ' + key + ' (' + schema_key + ' ' + fields[schema_key].value + ' PRIMARY KEY, position INTEGER, text VARCHAR)'
    # and now we can return the statements
    return statements

"""
We want to be able to take what would normally be used to index solr and
generate upsert statements from it. This is what the next function is going to
do.

But first we are going to create a class which takes one of those xml files
we would normally upload to solr, and instead parses them into several field
extractors.
"""

from xmlextractor import XMLExtractor
from markupcreater import StructuredDocument
from fieldextractor import FieldExtractor

class DocumentExtractor:

    def __init__(self, directory=''):
        self.xml_extractor = XMLExtractor(directory)

    def InputFile(self, file):
        self.xml_extractor.InputFile(file)

    def splitDocuments(self):
        # first we create the document
        self.documents = []
        self.xml_extractor.CreateDocument()
        for node in self.xml_extractor.document.nodes:
            if node.name == 'add':
                for child in node.children:
                    structured_doc = StructuredDocument()
                    structured_doc.nodes.append(child)
                    self.document.append(structured_doc) # appending all doc nodes

    def createFieldExtractors(self):
        # this will go through self.documents
        self.extractors = []
        for document in self.documents:
            field_extractor = FieldExtractor()
            field_extractor.ExtractFields(document)
            self.extractors.append(field_extractor)


def GenerateUpsertStatements(self, schema_ingestor, document_extractor):
    """
    So what the schema ingester is going to allow us to do is note how
    to handle each of the fields. add_docs_file is
