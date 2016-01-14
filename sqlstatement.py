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

class Select(Verbose):
    """
    SELECT
        * field names
        * From
            * table names
        * Where
            * conditional statements
            * logical joins and groupings
        * GroupBy
            * field names
        * Having
            * conditional statements
        * OrderBy
            * field names with optional ASC, DSC
    """

    def __init__(self):
        self.select_from_expression = re.compile('(?i)SELECT\s{1,}([\w\W][\w\W]*[^\s])\s{1,}FROM\s{1,}([\w\W][\w\W]*[^\s])')
        # this re grabs a match 'SELECT <text> FROM <text>' insensitive of case
        # the two texts are the two groups the match will have. The text is stripped of white space
        self.where_expression = re.compile('(?i)\s(WHERE)\s')
        self.having_expression = re.compile('(?i)\s(HAVING)\s')
        self.groupby_expression = re.compile('(?i)\s(GROUPBY)\s')
        self.orderby_expression = re.compile('(?i)\s(ORDERBY)\s')
        self.from_expression = re.compile('(?i)\s(FROM)\s')
        self.select_expression = re.compile('(?i)\s(SELECT)\s')
        self.expressions = [self.where_expression, self.having_expression,
            self.groupby_expression, self.orderby_expression, self.from_expression,
            self.select_expression]
        self.other_expressions = [self.where_expression, self.having_expression,
            self.groupby_expression, self.orderby_expression]
        self.other_expression_names = ['WHERE', 'HAVING', 'GROUPBY', 'ORDERBY']

    def findCommandGroups(self, statement):
        # this function will go through a statement and return a dictionary
        # with commands as keys and the text following the command (and before
        # the next if applicable) as the value

        # this is the initialized we will be returning
        command_dictionary = {'SELECT' : '', 'FROM' : '', 'WHERE' : '', 'HAVING' : '',
            'GROUPBY' : '', 'ORDERBY' : ''}
        match = re.search(self.select_from_expression, statement)
        # check to make sure that we have a match
        if not match:
            raise Issue("statment is not a valid Select Statement, doesn't match SELECT <text> FROM <text>")
        # our select text is in the match's first groups
        select_text = match.group(1)
        # now we check to make sure no commands are in select_text
        for expression in self.expressions:
            temp_match = re.search(expression)
            if temp_match:
                raise Issue('select command inputs have a sql command in them!')
        # we are all good here
        command_dictionary['SELECT'] = select_text
        # next we need to handle the From expression
        # first we get the text after the from
        other_text = match.group(0)
        # next we make sure there are not extra froms
        if re.search(self.from_expression, other_text):
            raise Issue('At least two from commands in your sql statement')
        # now we go through and find the first instances of each other command
        # if they exist and we find the starting index of the command
        other_list = []
        for i in range(0, len(self.other_expressions)):
            temp_match = re.search(self.other_expressions[i], other_text)
            if temp_match:
                # okay the starting index is going to be the start of the first group
                other_list.append((self.other_expression_names[i], temp_match.start(1)))
        # now we will first go through and sort them out
        other_list = self.sortOtherList(other_list)
        # now we go ahead will go ahead and chop things up
        # first we get the From text
        from_text = other_text[:other_list[0][1]].strip()
        for expression in self.expressions:
            if re.search(expression, from_text):
                raise Issue('command found in FROM input')
        command_dictionary['FROM'] = from_text
        # now we go and get the rest
        for i in range(0, len(other_list)):
            name = other_list[i][0]
            start_index = other_list[i][1]
            text = other_text[start_index + len(name):other_list[i+1] or len(other_text)]
            text = text.strip()
            for expression in self.expressions:
                if re.search(expression, text):
                    raise Issue('command found in %s input' % name)
            command_dictionary[name] = text
        # and we are done so we can now return the dictionary!
        return command_dictionary

    def sortOtherList(self, other_list):
        # this sorts the other_list created in findCommandGroups. It sorts by ascending
        # value of each elements object at the index 1
        made_switch = True
        while made_switch:
            new_list = []
            made_switch = False
            for i in range(1, len(other_list)):
                # so when we find an element if it has a smaller value
                # then the previous element, we append it to new list
                # if it doesn't then we set add the last element and set it
                # as the new one
                if other_list[i][1] < other_list[i-1][1]:
                    new_list.append(other_list[i])
                    made_switch = True
                else:
                    new_list.append(other_list[i-1])
            other_list = new_list
        return other_list

    """
    Now that we have isolated the groups and checked to make sure there are only
    the commands (and number of commands) that we expect, we now need to extract
    each of these pieces
    """

    def extractSelectCommand(self, select_text):
        # select text should be the text following the select command (stripped)
        # and before the next command (from) will be using regular expressions
        # here as well.
