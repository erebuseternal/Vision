# Python File sqlstatement.py

"""
This next class is going to be the python object representation of an SQL
(specifically phoenix) statement. It will be able to parse an SQL statement
and represent it as an object and then export that SQL statement afterwords.

An SQL statement is essentially composed of a number of pieces. For example
in a create statement there is the name and the schema given. In a select
statement, there is the Select part, the Where, the From, etc. But for each
type of statement there are different parts. So that is where we begin,
by outlining the parts.

CREATE, SELECT, DELETE, UPSERT (these will be what I handle for now)

CREATE                              UPSERT
    * table name                        * table name
    * schema                            * given field order
        * fields                        * values
        * constraints

SELECT                              DELETE
    * field names                       * table_name
    * From                              * Where
        * table names                       * conditional statements
    * Where                                 * logical joins and groupings
        * conditional statements
        * logical joins and groupings
    * GroupBy
        * field names
    * Having
        * conditional statements
    * OrderBy
        * field names with optional ASC, DSC
"""

from functions import *

class Field:
    """
    This class represents a single field that would show up in a CREATE
    statement schema. Therefore it has a name, a type, and constraints

    We are going to allow this class to take in such a line from a CREATE
    statement and pull out all of these pieces
    """

    def __init__(self, line=None):
        self.extract(line)

    def extract(self, line):
        if not line:
            return
        # we are going to get the name, the type, and the constraints
        # we assume there are no commas anywhere on the line.
        chunk = chunkGenerator(line, 3) # we want to split our line into three pieces
        self.name = next(chunk)
        self.type = next(chunk)
        self.constraints = next(chunk)

    def __repr__(self):
        return '%s %s %s' % (self.name, self.type.upper(), self.constraints.upper())

    def __str__(self):
        return self.__repr__()

class Create(Verbose):
    """
    This class will represent a create statement. As such it will have the pieces
    outlined here:
        * table name
        * fields      \ these two are the schema
        * constraints /
        * statement - the actual string itself
    """
    table_name = None
    fields = []
    constraints = []
    statement = None

    def __init__(self, verbose=0):
        self.v = verbose
        self.VP('Initialized Create Object')

    def UploadStatement(self, statement):
        # this takes an sql statement and uploads it to this object
        # start by reinitializing these attributes
        self.VP('Entering UploadStatement with statement %s' % statement)
        self.table_name = None
        self.fields = []
        self.constraints = []
        self.statement = None
        self.VP('Reset attributes', 2)
        self.statement = statement
        self.VP('Set statement to %s' % statement, 2)
        statement = statement.strip()
        # now first we check to make sure that the operation is indeed CREATE
        chunk = chunkGenerator(statement, 4)   # this will allow us to grab
            # the first two commands, the table name, and the schema as chunks
        self.VP('chunkGenerator Initialized', 2)
        command1 = next(chunk)
        self.VP('first command: %s' % command1, 2)
        command2 = next(chunk)
        self.VP('second command: %s' % command2, 2)
        if not (command1.upper() == 'CREATE' and command2.upper() == 'TABLE'):
            raise Issue('CREATE TABLE command absent or erroneously spelled')
        self.VP('Commands checked out', 2)
        # now we can go on to get the table name
        table_name = next(chunk)
        self.VP('Third chunk: %s' % table_name, 2)
        # we quickly need to make a check that there is a space between
        # the table name and the schema
        parens_index = table_name.find('(')
        if parens_index != -1:
            self.VP('Found parens', 2)
            # in this case we need to split table_name into the actual name and
            # the schema
            schema, table_name = table_name[parens_index:], table_name[0:parens_index]
        else:
            # in this case the name and schema are separated by a space so we
            # make a last call to the chunk generator
            self.VP("Didn't find parens", 2)
            schema = next(chunk)
        # next we remove the parenthesis
        self.table_name = table_name
        self.VP('Split acheived: table: %s, schema: %s' % (table_name, schema), 2)
        if schema[-1] == ';':
            schema = schema[1:-2]
        else:
            schema = schema[1:-1]
        self.VP('Schema parens removed: %s' % schema, 2)
        # now we split the schema by commas
        schema = schema.split(',')
        for line in schema:
            line = line.strip()
            if line[0:10].upper() == 'CONSTRAINT':
                self.VP('line - %s - is a constraint' % line, 2)
                self.constraints.append(line)
            else:
                self.VP('line - %s - is a field' % line, 2)
                self.fields.append(Field(line))

    def DownloadStatement(self):
        # this takes the properties found within and creates a statement which
        # it then sets on itself
        self.VP('Entering DownloadStatement')
        if not self.table_name:
            raise Issue('No table name specified')
        self.VP('table name is: %s' % self.table_name, 2)
        if self.fields == []:
            raise Issue('No fields found')
        self.VP('fields found', 2)
        statement = 'CREATE TABLE %s ' % self.table_name
        schema = ''
        for field in self.fields:
            self.VP('adding field: %s' % field, 2)
            schema = '%s %s,' % (schema, field)
        for constraint in self.constraints:
            self.VP('adding constraint: %s' % field, 2)
            schema = '%s %s,' % (schema, constraint)
        # clip the front space and the trailing comma
        schema = schema[1:-1]
        self.VP('schema after clipping: %s' % schema, 2)
        statement = statement + '(' + schema + ')'
        self.VP('final statement: %s' % statement, 2)
        self.statement = statement

    def AddField(self, field):
        self.fields.append(field)

    def AddConstraint(self, constraint):
        self.constraints.append(field)

    def SetTableName(self, name):
        self.table_name = name
