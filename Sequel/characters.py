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
