# Python File characters.py (part of Sequel)

# for general problem handling
class Issue(Exception):
    def __init__(self, problem):
        self.problem = problem
    def __str__(self):
        return 'ERROR: the problem was: %s' % self.problem

"""
Herein are objects representing all of the declarative SQL statements I will be
using. I will be using them to represent SQL commands in my code. Refer to notes
on why I have decided to take this path. Each object has two requirements. First
that it has as its own structure the structure of the SQL statement it
represents. Secondly that it has a speak function, which allows the object
to return itself in the language of SQL: as a string.

Also, I'm going to have __str__ return a call to Speak
"""

"""
Our base class
"""

class Character:
    def Speak(self):
        # it is this method which should take the various structure and data
        # within the object and return an SQL statement in string form.
        # nitty gritty: return the object's representative string
                                        # so that you can know when you forgot
        return 'A Generic Character'    # to override this method :)

    def __str__(self):
        # Speak is the string representation of this object after all :P
        return self.Speak()

"""
A CREATE TABLE SQL command is pretty simple. It has:
    * table name
    * schema fields
        * field name
        * field type
        * field constraint
    * schema constraints
        * constraint name
        * constraint
"""

class SchemaField:
    """
    This class represents a schema field
    """

    def __init__(self, name, type, constraint=None):
        self.name = name
        self.type = type
        self.constraint = constraint

    def __str__(self):
        # these are here so that only writing out the SQL statement
        # and not each of the statements individual pieces with all of
        # their details matters
        if self.constraint:
            return '%s %s %s' % (self.name, self.type, self.constraint)
        else:
            return '%s %s' % (self.name, self.type)

class SchemaConstraint:
    """
    This class represents a schema constraint
    """

    def __init__(self, name, constraint):
        self.name = name
        self.constraint = constraint

    def __str__(self):
        # these are here so that only writing out the SQL statement
        # and not each of the statements individual pieces with all of
        # their details matters
        return 'CONSTRAINT %s %s' % (self.name, self.constraint)

class Create(Character):
    table_name = None
    fields = []
    constraints = []

    def SetTableName(self, table_name):
        self.table_name = table_name


    def AddField(self, field):
        if isinstance(field, SchemaField):
            self.fields.append(field)
        else:
            raise Issue("the field you tried to add isn't an instance of SchemaField")

    def AddConstraint(self, constraint):
        if isinstance(constraint, SchemaConstraint):
            self.constraints.append(constraint)
        else:
            raise Issue("the constraint you tried to add isn't an instance of SchemaConstraint")

    def Speak(self):
        # first let us construct the schema part
        schema_string = ''
        # first the fields
        for field in self.fields:
            schema_string = '%s %s,' % (schema_string, field)  # note we are taking
                                            # advantage of the __str__ override
                                            # for fields (same will be said for
                                            # constraints)
        for constraint in self.constraints:
            schema_string = '%s %s,' % (schema_string, constraint)
        # now note that there will be an unneeded space at the beginning of
        # schema_string and a most unwanted comma at the end, so we will clip
        # those off now
        scema_string = schema_string[1:-1]
        # now we have all the pieces so we can assemble them!
        statement = 'CREATE TABLE %s (%s)' % (self.table_name, schema_string)
        # and we are all done so we return this string
        return statement

"""
UPSERT
    * table name
    * given field order
    * values

So the way that we are going to do this is by keeping table_name and then
the key value pairs of field -> value. This seems the most natural way of
capturing the structure of an UPSERT.
"""

class Upsert(Character):
    table_name = None
    values = {} # this is the dictionary that is field -> value

    def SetTableName(self, table_name):
        self.table_name = table_name

    def AddValue(self, field_name, value):
        values[field_name] = value

    def Speak(self):
        # we need to put together the field list and the value list together
        # we definitely want to do this at the same time, because the values
        # need to come in the same order as the fields come
        field_text = ''
        value_text = ''
        for field_name in self.values:
            field_text = field_text + ' ' + field_name + ','
            value_text = '%s %s,' % (value_text, values[field_name])
        # now we need to clip the first space and last comma from each of these
        # and then we are ready to go!
        field_text = field_text[1:-1]
        value_text = value_text[1:-1]
        # ready to go! :D
        statement = 'UPSERT INTO %s(%s) VALUES (%s)' % (self.table_name, field_text, value_text)
        return statement

"""
SELECT
    * fields
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

Now each of these pieces can be a wee bit complicated so let's go through them
carefully :)
"""

"""
Fields

first off they have a name. Then fields in the select statement can have a few
'values':
    * function
    * expression
    * constant value
    * field name
and they can have keywords like Distinct

So we would like this kind of object:
    * name
    * keywords
    * content - which is only one of the following
        * value (i.e. constant)
        * function
            * function name
            * field name (that goes in the function)
        * field name

I do not expect to use expressions at all. So I'm going to leave that out for now

Finally, the value can have a table attached to it
"""

class QueryField:
    name = None
    content = None
    type = None # the type of content
    table = None    # the table from which we get the field specified
                    # if there is one
    keywords = []

    def SetName(self, name):
        self.name = name

    def SetField(self, field_name, as_name=True):
        # this sets the content as a field name. If as_name is true
        # it also sets name to the field_name
        self.content = field_name
        self.type = 'FIELD'
        if as_name:
            self.name = field_name

    def SetValue(self, value):
        # this sets the content as a constant value
        self.content = value
        self.type = 'VALUE'

    def SetFunction(self, function, argument):
        # this sets the content as a function
        self.content = {'function' : function, 'argument' : argument}
        self.type = 'FUNCTION'

    def SetTable(self, table):
        self.table = table

    def AddKeyword(self, keyword):
        self.keywords.append(keyword)

    def RemoveKeyword(self, keyword):
        self.keywords.pop(keyword)

    def prepareField(self):
        # this puts everything around the field that's needed
        if self.table:
            product = '%s.%s' % (self.table, self.content)
        else:
            product = self.content
        for keyword in self.keywords
            product = '%s %s' % (keyword, product)
        return product

    def __str__(self):
        if self.type == 'FUNCTION':
            return '%s %s(%s)' % (self.name, self.content['function'], self.prepareField(self.content['argument'])
        elif self.type == 'VALUE':
            return '%s %s' % (self.name, self.content)
        elif self.type == 'FIELD':
            if self.name == self.content:
                return self.prepareField(self.content)
            else:
                return '%s %s' % (self.name, self.prepareField(content))
