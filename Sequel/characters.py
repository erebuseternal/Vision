# Python File scratch.py

from copy import deepcopy

# for general problem handling
class Issue(Exception):
    def __init__(self, problem):
        self.problem = problem
    def __str__(self):
        return 'ERROR: the problem was: %s' % self.problem

class TypeIssue(Issue):
    def __init__(self, problem_type, required_type):
        self.required_type = required_type
        self.problem_type = problem_type
    def __str__(self):
        return 'TYPE ERROR: expected type was %s, you tried using type %s' % (self.required_type, self.problem_type)

def checkType(object, required_type):
    # this raises an error if the types don't match (or there is no proper inheritance link)
    if not isinstance(object, required_type):
        raise TypeIssue(type(object), required_type)

def checkTableLegitimacy(table):
    if not table.IsLegitimate():
        table_name = table.name
        table_field_number = len(table.fields)
        table_pk = table.pk
        raise Issue('Input table is not legitimate - name: %s, #fields: %s, pk: %s' % (table_name, table_field_number, table_pk))


class Type:
    solr = 'GenericType'
    phoenix = 'GenericType'
    needs_separate_table = False  # this indicates whether a separate table is needed
                            # for this type
    piece_type = None

    def TurnPhoenix(self, solr_value):
        # override this
        return solr_value

    def TurnSolr(self, phoenix_value):
        # override this
        return phoenix_value

class SideType(Type):
    needs_separate_table = True
    piece_type = Type()

    def Break(self, solr_value):
        # should return an array of values
        return [solr_value]

    def Combine(self, phoenix_value):
        # should patch back together the value
        return phoenix_value[0]

class Bool(Type):
    solr = 'Bool'
    phoenix = 'TINYINT'

    def TurnPhoenix(self, solr_value):
        truths = [1, 't', 'T', '1']
        if solr_value in truths:
            return 1
        else:
            return 0

    def TurnSolr(self, phoenix_value):
        truths = ['1', 1]
        if phoenix_value in truths:
            return 1
        else:
            return 0

class Date(Type):
    solr = 'DateRange'
    phoenix = 'DATE'

    def TurnPhoenix(self, solr_value):
        if solr_value.find('T') == -1:
            return solr_value   # it is already in the phoenix form
        date = solr_value[:10] # cutting off T at end of date in solr value
        time = solr_value[11:-1] # cutting off Z at end of solr value
        value = date + ' ' + time
        return value

    def TurnSolr(self, phoenix_value):
        if phoenix_value.find('T') != -1:
            return phoenix_value
        date = phoenix_value[:10]
        time = phoenix_value[11:]   # through these two steps we cut out the space between
                            # date and time
        value = date + 'T' + time + 'Z'
        return value

class String(Type):
    solr = 'Str'
    phoenix = 'VARCHAR'

class Text(SideType):
    solr = 'Text'
    piece_type = String()

    def Break(self, solr_value):
        array = []
        if len(solr_value) <= 255:
            array.append(solr_value)
            return array
        end = 0
        for i in range(255, len(solr_value), 255):
            array.append(solr_value[i - 255: i])
            end = i
        if end < len(solr_value):
            array.append(solr_value[end:])
        return array

    def Combine(self, phoenix_value):
        value = ''
        for string in phoenix_value:
            value = '%s%s' % (value, string)
        return value

class Double(Type):
    solr = 'TrieDouble'
    phoenix = 'DOUBLE'

class Int(Type):
    solr = 'TrieInt'
    phoenix = 'INTEGER'

class Float(Type):
    solr = 'TrieFloat'
    phoenix = 'FLOAT'

class Long(Type):
    solr = 'TrieLong'
    phoenix = 'BIGINT'

class Typer:
    types = [Type(), Bool(), Date(), String(), Text(), Double(), Int(), Float(), Long()]

    def Type(self, type_name, is_solr=True):  # this gets the type given a type name
        # and an indicator whether the name comes from solr or phoenix. defualt is solr
        if is_solr:
            for type in self.types:
                if type.solr == type_name:
                    return type
            raise Issue('Your solr type %s did not match any types' % type_name)
        else:
            for type in self.types:
                if type.phoenix == type_name.upper():
                    return type
            raise Issue('Your phoenix type %s did not match any types' % type_name)

class Field:
    """
    This class represents a field
    """

    def __init__(self, name, type, is_pk=False):
        self.name = name
        checkType(type, Type)   # just to make sure this is a subclass of Type
        self.type = type
        self.is_pk = is_pk

    def Schema(self):
        # these are here so that only writing out the SQL statement
        # and not each of the statements individual pieces with all of
        # their details matters
        if self.is_pk:
            return '%s %s PRIMARY KEY' % (self.name, self.type.phoenix)
        else:
            return '%s %s' % (self.name, self.type.phoenix)

"""
The table is the centerpiece of essentially everything we will be doing.
A table of course has:
    * name
    * fields
    * a primary key

    Fields within a table are dealt with based upon their names. Therefore
    we will save the fields in a dictionary object with the keys being field
    names.

    We will also save whichever field is the primary key under self.pk
    it will be initialized to None.

    Finally there will be a method that can be used to check that a table
    has all of the above properties
"""

class Table:

    def __init__(self, name):
        self.name = name
        self.fields = {}
        self.has_pk = False
        self.pk = None

    def IsLegitimate(self):
        # this will return true if we a have a primary key, fields, and a name
        # it will return false if any of those are not true
        if not self.pk:
            return False
        if len(self.fields) == 0:
            return False
        if not self.name:
            return False
        return True

    def AddField(self, field):
        # first we check to make sure that field is a field type
        checkType(field, Field)
        # first we check to see if we are adding a field with a name already
        # used by another field
        if field.name in self.field_dictionary:
            raise Issue('Field name already taken')
        # next we check to see if we are trying to add a primary key
        if field.is_pk:
            # if we already have one, then we raise an Issue
            if self.pk:
                raise Issue('Trying to add a redundant Primary Key')
            else:
                # otherwise we add the field and set it as the primary key
                self.fields[field.name] = field
                # and we let the object know it has a primary key
                self.pk = field
        else:
            # if it is just a normal field, we just add it
            self.fields[field.name] = field

    def RemoveField(self, field_name):
        # NOTE: this returns a NEW table with the field removed
        # first we check to make sure the field is in fields. If it isn't
        # the person is probably confused so we throw an error
        if not field_name in self.fields:
            raise Issue('Attempted to remove a non-existant field')
        else:
            # otherwise we make a copy of the table, remove the field,
            # and return that table
            new_table = deepcopy(self)
            del new_table.fields[field_name]
            return new_table

    def Split(self):
        # this methods splits off fields needing new tables and creates a SideTable
        # for each. It generates a list from the original table (without those fields
        # which have been split off) and the side tables. It returns this list.
        # the 'main' table is first in the list
        tables = [self] # we initialize the list with our main table
        # we loop through the fields
        for field_name in self.fields:
            field = fields[field_name]
            if field.type.needs_separate_table:   # we see if the field needs a separate table
                # if so, first we remove the field from the main table
                tables[0] = tables[0].RemoveField(field_name)
                # then we create a sidetable
                side_table = SideTable(self, field)
                # and we add it the tables list
                tables.append(side_table)
        return tables

"""
This class represents a table with a very specific schema. These tables are created
for fields who are of a type that needs a separate table. Such fields have their
solr representation broken into pieces, so that it can be stored in hbase. This
is what warrents the extra table.

The schema of the new table is:
    name: name of the field used to generate the side table
    fields:     primary key of the table from which the field came
                a field named position with type Int which keeps track of
                    the order of the pieces the field's value has been broken into
                a field named piece, which contains a piece of the original
                    field value. It has the piece type given by the original field's
                    type

Because of the very strict nature of the schema, we will set up the entire table
right on initilialization, and we will initialize with the generating field and
the 'parent' table
"""

class SideTable(Table):

    def __init__(self, generating_field, parent_table):
        # first we do a type check
        checkType(parent_table, Table)
        checkType(generating_field, Field)
        # then we make sure the table is legitimate
        checkTableLegitimacy(table)
        # now we set the name of our table and initialize the table
        name = generating_field.name
        Table.__init__(self, name)
        # we set the following for reference
        self.generating_field = generating_field
        # now we setup our fields
        self.setupTableFields(generating_field, parent_table)

    def setupTableFields(self, generating_field, parent_table):
        # this fields just sets up our fields on this table
        # so first we create them
        pk = parent_table.pk
        position = Field('position', Int())
        # we get the piece type for our piece field
        piece_type = generating_field.type.piece_type
        piece = Field('piece', piece_type)
        # and now we go ahead and add all of the fields
        self.AddField(pk)
        self.AddField(position)
        self.AddField(piece)


"""
Because, when concerning solr data, we wish to use HBase primarily for
backups, we will only concern ourselves with single tables. This also
greatly simplifies this code. And, as a final note, HBase is not great for
joins anyways. So this seems like a warranted limitation.

As such, at the center of every statement, there will be a single table.
And therefore, we will initialize any statement with the table it will be
using. The following then gives us exactly that, and our statements can inherit
from it.

The other piece that every Character must have is a Split method. This method
will split the table it has been set with and return a list of Characters -
one for each of the resulting tables. These Characters will then be the ones
that are executed. This means we initialize a character with the solr like form
and data and then there is an easy way to break that up into the statements that
will actually be used.

As a general rule, the Character generated from the 'main' table after a split
should be the first in the list of Characters returned.

Finally, the string representation of a character should be the Phoenix command
it represents.
"""

class Character:

    def __init__(self, table):
        # first we do a type check
        checkType(table, Table)
        # then we check that the table is legitimate
        checkTableLegitimacy(table)
        # and since everything checks out, we set the table
        self.table = table

    def Split(self):
        pass

"""
The following class is the Character that handles Create Table statements.
It of course is simply initialized with a table. And its split is as simple
as splitting the table and then creating Creates for each table.
"""

class Create(Character):

    def Split(self):
        # first we split the table
        tables = self.table.Split()
        # now we create a Create for each table
        creates = []    # the list that will contain each of these creates
        for table in tables:
            create = Create(table)
            creates.append(create)
        return creates


    def __str__(self):
        # this of course needs to return the phoenix command represented by a Create
        # so first we make the schema definition part of things
        schema_string = ''
        for field_name in self.table.fields:
            schema_string = '%s%s, ' % (schema_string, fields[field_name].Schema())
        # we cut off the last comma and space
        schema_string = schema_string[:-2]
        # and now we put everything together
        line = 'CREATE TABLE %s (%s)' % (self.table.name, schema_string)
        return line

"""
Next, for upserts and conditions, we are going to need a value class.
We are going to have the values take a type, so that we can ensure the
person is paying attention to what types they are inputting and all of that jazz.
Remember a value is more than just its representation.

Also note that we expect you to only work with the solr values, so this is
going to assume that you have exactly that. (Note that the whole point of this
code is so that you can work only in the solr representation)
"""

class Value:

    def __init__(self, solr_representation, type):
        checkType(type, Type)
        self.type = type
        self.representation = solr_representation

    # this will print out the converted value
    def Content(self):
        # here we just need to convert the solr representation and print that
        phoenix_representation = self.type.TurnPhoenix(self.representation)
        return str(phoenix_representation)

"""
In addition to a table, the Upload (Upsert) statement has a set of values.
These values are tied each to a different field, so we will hold them in this
Character in a dictionary keyed by field_names
"""

class Upload(Character):

    def __init__(self, table):
        Character.__init__(self, table)
        self.values = {}    # keys should be field names, and values Value objects

    def Split(self):
        """
        1. Split table
        2. Isolate the main table
        3. Add all of the values to the main table in its own upload statement
        For each of the side tables
        4. Get the associated values
        5. Break the value for the generating field based on its type
        6. Create uploads for every piece of the value and do this for each
            side table using the pk
        7. return them uploads
        """
        # 1
        tables = self.table.Split()
        # 2
        main_table = tables[0]
        # 3
        main_upload = Upload(main_table)
        for field_name in main_table.fields:
            main_upload.SetValue(field_name, self.values[field_name])
        uploads = [main_upload] # initialize the list we will be returning
        if len(tables) == 1:    # we check to see that there are side_tables
            return uploads
        # 4
        side_tables = tables[1:]    # we get the side tables
        pk_name = self.table.pk.name    # we need the primary key and its value
        pk_value = self.values[pk_name] # for all of the side_table upserts
        for table in side_tables:
            # first we get the value associate with the generating field
            generating_field_name = table.name
            value = self.values[generating_field_name]
            # then we break the value according to its type
            # 5
            pieces = self.value.type.Break(value.Content())
            piece_type = self.value.type.piece_type
            # we initialize the value of position
            position = 0
            # 6
            # we create an upsert for each piece
            for piece in pieces:
                upload = Upload(table)
                # we create the value for position
                position_value = Value(position, Int())
                # we create the value for the piece
                piece_value = Value(piece, piece_type)
                # we upload the values
                upload.SetValue(pk_name, pk_value)
                upload.SetValue('position', position_value)
                upload.SetValue('piece', piece)
                # we reset position and append the new upload
                position = position + 1
                uploads.append(upload)
        # 7
        return uploads


    def SetValue(self, field_name, value):
        checkType(value, Value)
        # next we check to make sure the field name is valid
        if not field_name in self.table.fields:
            raise Issue('Setting value to a non-existant field')
        # we check that the type for the field and the type for the
        # value are the same
        if not fields[field_name].type == value.type:
            raise Issue('Value and field have inconsistent types')
        # so we know that we are okay and we go ahead and add the value
        self.values[field_name] = value

    def Speak(self):
        # first we check that all fields have a value
        for field_name in self.table.fields:
            if not field_name in self.values:
                raise Issue('Value missing for at least field: %s' % field_name)
        # so know that we know we are good, we go ahead and create the value string
        # and the field string at the same time
        field_string = ''
        value_string = ''
        for field_name in fields:
            field_string = '%s%s, ' % (field_string, field_name)
            value_string = '%s%s, ' % (value_string, self.values[field_name].Content())
        # now we cut off the extra comma and space from both
        field_string = field_string[:-2]
        value_string = value_string[:-2]
        # and now we can create our line
        line = 'UPSERT INTO %s(%s) VALUES (%s)' % (self.table.name, field_string, value_string)
        return line



"""
The next couple classes depend upon a where clause. This requires us to have some notion
of conditions. Note that I am assuming that we do not do groupings or analysis type
actions on the data in our statements. This is because not all of them can be used as
such, and so for consistency, if you want to use such functionality, you need to
go to a lower level.
"""

class Condition:

    def __init__(self):
        self.first_operand = None
        self.second_operand = None
        self.operator = None

    def AddOperator(self, operator):
        self.operator = operator

    def AddFirstOperand(self, operand):
        # the first operand has to be a field
        checkType(operand, Field)
        self.first_operand = operand

    def AddSecondOperand(self, operand):
        # the second operand has to be a value or a field
        if not (isinstance(operand, Field), isinstance(operand, Value)):
            raise Issue('Entered operand is not of type Field or Value')
        self.second_operand = operand

    def __str__(self):
        if isinstance(self.second_operand, Field):
            return '%s %s %s' % (self.first_operand.name, self.operator, self.second_operand.name)
        else:
            # in this case we are dealing with a value as the second operand
            return '%s %s %s' % (self.first_operand.name, self.operator, self.second_operand)

"""
Then for where and having we are going to do something a little different. We
are going to represent them by a set of nodes.

The idea is the following: each top level node will either have a QueryCondition
in it, or will be empty. If it is empty it will have children, each of the children
being part of one group that needs to get treated first. The children of this
node act like a new level, so there can be groups inside. But this is how
we are going to work with the conditional stuff. Finally, each node that has a
next sibling is going to have an operator as well. This is how the two siblings
are joined.
"""

class Node:

    def __init__(self):
        self.parent = None
        self.children = []
        self.sibling = None # assumed to be the next sibling
        self.operator = None
        self.condition = None

    def SetCondition(self, condition):
        if not isinstance(condition, Condition) and condition:
            raise Issue('entered condition is not an instance of Condition and is not None')
        self.condition = condition

    def CreateChild(self, operator='AND'):  # note the default operator is AND
                                            # this default is only used if we are
                                            # adding a child to a parent with children
        child = Node()
        child.parent = self
        if len(self.children) > 0:
            self.children[-1].sibling = child
            self.children[-1].operator = operator
        self.children.append(child)
        return child

    def CreateSibling(self, operator='AND'):
        if self.parent:
            return self.parent.CreateChild(operator)
        else:
            sibling = Node()
            self.sibling = sibling
            self.operator = operator
            return sibling

    def SetOperator(self, operator):
        self.operator = operator

    # now the convenience method. This method will
    # construct a string using itself, its children,
    # its siblings and the operators for all. It starts
    # from itself and goes from there.
    # I'm going to do this by creating a function that
    # prints stuff for the node itself and then calls
    # itself on its first child and its sibling. And then joins
    # the result as needed
    def createString(self):
        if not self.sibling:
            if self.condition:
                return '%s' % self.condition
            else:
                children_string = self.children[0].createString()
                return '(%s)' % children_string
        else:
            if not self.operator:
                raise Issue('operator is missing and this node has a sibling')
            next_string = self.sibling.createString()
            if self.condition:
                return '%s %s %s' % (self.condition, self.operator, next_string)
            else:
                children_string = self.children[0].createString()
                return '(%s) %s %s' % (children_string, self.operator, next_string)

    def __str__(self):
        return self.createString()

"""
This class represents and has all the methods needed for a where clause
"""

class Where:

    def __init__(self):
        self.node = None
        self.last_added_node = None
        self.group_entry = False

    def AddCondition(self, condition, operator='AND'):
        # operator is only used once at least one condition is present in the where
        # and gets attached to the last added condition
        if not self.node:
            new_node = Node()
            new_node.SetCondition(condition)
            self.node = new_node
            self.last_added_node = new_node
        else:
            if self.last_added_node.condition:
                # create a sibling for the last node
                new_node = self.last_added_node.CreateSibling()
            else:   # this is the case where the last one created was a group
                    # or we just exited a group
                if self.group_entry:
                    # just entered a group
                    new_node = self.last_added_node.CreateChild()
                else:
                    # just exited
                    new_node = self.last_added_node.CreateSibling()
            # set the nodes condition
            new_node.SetCondition(condition)
            # set the operator on the last condition
            self.last_added_node.SetOperator(operator)
            self.last_added_node = new_node


    def AddGroup(self, operator='AND'):
        self.AddWhereCondition(None, operator)
        self.self.group_entry = True

    def ExitGroup(self):
        # all we have to do is go back up a level
        self.last_added_node = self.last_added_node.parent
        self.self.group_entry = False

    def __str__(self):
        return str(self.node)

"""
When a conditional statement comes up in a statement concerning a table that is actually composed
of a main table and many side tables, we need to be able to transfer the condition
on the main table to a condition for the side tables. The easiest way of doing
this is to find the keys that satisfy the condition on the main table and use
that to create our condition for the side_tables. The next two classes allow
us to do exactly that.

The first is a statement that will find those keys.
The second is the statement that will use the first to find the values from a side
table.

The first takes a statement and uses the table and condition to generate the needed
query.
"""

# this class if for finding a key based on a where statement
class KeyFinderQuery:

    # we initialize with a statement
    def __init__(self, statement):
        # first we check we are ingesting a character with a where statement
        checkType(statement, WhereCharacter)
        # then we grab the needed components
        self.table = statement.table
        self.where = statement.where
        self.pk = self.table.pk

    def Speak(self):
        # here we generate the statement itself
        if self.where:
            line = 'SELECT %s FROM %s WHERE %s' % (self.pk.name, self.table.name, self.where)
        else:
            line = 'SELECT %s FROM %s' % (self.pk.name, self.table.name)
        return line

class KeyBasedStatement:

    def __init__(self, side_table, key_finder, statement_type):
        # this takes the side table we will be querying on
        # the key_finder query which we will use as a condition
        # and a boolean that tells us if this request for a statement
        # of this form came from a select or a delete
        # first we do type checks
        checkType(side_table, SideTable)
        checkType(key_finder, KeyFinderQuery)
        checkType(original_statment, WhereCharacter)
        self.key_finder = key_finder
        self.side_table_name = side_table.name
        self.generating_field_name = self.side_table.generating_field_name.name
        if statement_type == Select:
            self.is_select = True
        else:
            self.is_select = False
        self.side_table_pk = side_table.pk.name

    def Speak(self):
        if not self.is_select:
            return 'DELETE FROM %s WHERE %s IN (%s)' % (self.side_table_name, self.side_table_pk, self.key_finder.Speak())
        else:
            # note that we order first by the key and then by the position
            # this is to keep things consistent so that the Executor knows
            # how to handle things
            return 'SELECT %s, value FROM %s WHERE %s IN (%s) ORDERBY %s, position ASC' % (self.side_table_pk, self.side_table_name, self.side_table_pk, self.key_finder.Speak(), self.side_table_pk)

"""
This is used when no where clause is present in a WhereCharacter
"""

class SimpleStatement:

    def __init__(self, side_table, statement_type):
        # this takes the side table we will be querying on
        # and a boolean that tells us if this request for a statement
        # of this form came from a select or a delete
        # first we do type checks
        checkType(side_table, SideTable)
        checkType(original_statment, WhereCharacter)
        self.side_table_name = side_table.name
        self.generating_field_name = self.side_table.generating_field_name.name
        if statement_type == Select:
            self.is_select = True
        else:
            self.is_select = False
        self.side_table_pk = side_table.pk.name

    def Speak(self):
        if not self.is_select:
            return 'DELETE FROM %s' % (self.side_table_name)
        else:
            # note that we order first by the key and then by the position
            # this is to keep things consistent so that the Executor knows
            # how to handle things
            return 'SELECT %s, value FROM %s ORDERBY %s, position ASC' % (self.side_table_pk, self.side_table_name, self.side_table_pk)

"""
The following class gives us the basis for a character which has a where clause.
Note that when creating conditions for this where clause, you should use
CreateCondition to make sure that you are actually using fields in the table,
and that the types of the operands match up.

In addition we add a special split that makes use of the above two classes
"""

class WhereCharacter(Character):

    def __init__(self, table):
        Character.__init__(self, table)
        self.where = Where()

    def GenerateKeyFinder(self):
        return KeyFinderQuery(self)

    def CreateCondition(self, field_name, second_operand, operator='='):
        # first we check that the entered field (for first operand spot)
        # exists in our table
        fields = self.table.GetFields()
        if not field_name in fields:
            raise Issue('Field was not found in the table')
        operand1 = fields[field_name]
        # next we check to see if the second operand is another field name
        # a string or and value
        if isinstance(second_operand, str):
            # we first check that the field is in the table
            if not second_operand in fields:
                raise Issue('Second Operand was a string but was not found in the table as a field')
            # we check to make sure the types are the same
            if not operand1.type == second_operand.type:
                raise Issue('input fields are of inconsistent types')
            # we set operand2
            operand2 = fields[second_operand]
        elif isinstance(second_operand, Value):
            # we check to make sure the types are the same
            if not operand1.type == second_operand.type:
                raise Issue('input field and value are of inconsistent types')
            # we set operand2
            operand2 = second_operand
        # now we can create a condition
        condition = Condition()
        condition.AddFirstOperand(operand1)
        condition.AddSecondOperand(operand2)
        condition.AddOperator(operator)
        return condition

    def AddCondition(self, condition):
        self.where.AddCondition(condition)

    def AddGroup(self):
        self.where.AddGroup()

    def ExitGroup(self):
        self.where.ExitGroup()

    def generateSideTableQueries(self):
        # here we are going to split the table and handle the side tables
        # essentially, we need to creat the key finder query and then
        # create key based statements for each
        tables = self.table.Split()
        type = type(self)
        # if there is only one entry in the table, there are no side tables
        # and so we return an empty list
        if len(tables) == 1:
            return []
        side_tables = tables[1:]
        statements = []
        # next we see if there is a where condition
        if self.where:
            # we generate a key finder query
            key_finder = KeyFinderQuery(self)
            # now we create one key based statement at a time
            for table in side_tables:
                key_based = KeyBasedStatement(table, key_finder, type)
                statements.append(key_based)
            return statements
        else:
            # if there is no where then we use a SimpleStatement
            for table in side_tables:
                simple = SimpleStatement(table, type)
            return statements


    def Split(self):
        # here when we split we create a class instance of the same
        # type as that of self for the 'main' table that results after
        # the split. For the side_tables, we first have to generate a
        # key finder query for all of them to use, and then we have
        # to
        tables = self.table.Split()
        type = type(self)
        main_table = tables[0]
        main_statement = type(main_table)
        fields = main_table.GetFields()
        for field_name in fields:
            if field_name in self.fields:
                main_statement.AddField(field_name)
        statements = [main_statement]
        if len(tables) > 1:
            side_tables = tables[1:]
            key_finder = self.GenerateKeyFinder()
            for table in side_tables:
                statement = KeyBasedStatement(type, table, key_finder)
                statements.append(statement)
        return statements


class Select(CompleteStatment):

    def __init__(self, table):
        WhereCharacter.__init__(self, table)
        self.fields = {}

    def AddField(self, field_name):
        fields = self.table.GetFields()
        if not field_name in fields:
            raise Issue('Trying to use a non existant field')
        self.fields[field_name] = fields[field_name]

    def Split(self):
        # here we create the main statement from the 'main' table
        # and then we call generateSideTableQueries to fill in the rest
        # of the list
        tables = self.table.Split()
        main_table = tables[0]
        main_statement = Select(main_table)
        # add the fields
        for field_name in main_table.fields:
            if field_name in self.fields:
                main_statement.AddField(field_name)
        # set the where
        main_statement.where = self.where
        statements = [main_statement]
        # now we get the rest of the statements
        rest = self.generateSideTableQueries()
        statements.extend(rest)
        return statements

    def Speak(self):
        field_string = ''
        for field_name in self.fields:
            field_string = '%s%s, ' % (field_string, field_name)
        field_string = field_string[:-2]
        # note the orderby for consistency in the executor
        if self.where:
            line = 'SELECT %s FROM %s WHERE %s ORDERBY %s' % (field_string, self.table.name, self.where, self.table.pk.name)
        else:
            line = 'SELECT %s FROM %s ORDERBY %s' % (field_string, self.table.name, self.table.pk.name)

class Delete(CompleteStatment)

    def Split(self):
        # here we create the main statement from the 'main' table
        # and then we call generateSideTableQueries to fill in the rest
        # of the list
        tables = self.table.Split()
        main_table = tables[0]
        main_statement = Delete(main_table)
        # set the where
        main_statement.where = self.where
        statements = [main_statement]
        # now we get the rest of the statements
        rest = self.generateSideTableQueries()
        statements.extend(rest)
        return statements

    def Speak(self):
        if self.where:
            line = 'DELETE FROM %s WHERE %s' % (field_string, self.table.name, self.where)
        else:
            line = 'DELETE FROM %s' % (field_string, self.table.name)

"""
We are going to work with phoenix through an interface. This means that we can
change the actual driver we use as time goes on. This interface has Connect and
Execute methods, and after execution, values can be accessed through Get and
we can call next to get the next value
"""

class Interface:

    def __init__(self):
        self.connection = None
        self.cursor = None

    def Connect(self, address):
        pass

    def Execute(self, statement):
        pass

    def Next(self):
        pass

    def Get(self, field_name):
        pass

    def Close(self):
        pass

class Executor:

    interface_type = Interface

    def __init__(self, statement, address):
        checkType(statement, SingleTableCharacter)
        self.statement = statement
        self.table = statement.table
        self.pk_name = self.table.pk.name
        self.statements = statement.Split()
        self.main_statement = self.statements[0]
        if len(self.statements) > 1:
            self.side_statements = self.statements[1:]
        else:
            self.side_statements = []
        self.address = address
        self.has_called_next = False

    def Execute(self):
        self.has_called_next = False
        if not isinstance(statement, Select):
            # here is is easy we just execute, there is nothing special to keep
            # track of
            interface = self.interface_type()
            interface.Connect(self.address)
            for statement in self.statements:
                interface.Execute(str(statement))
        else:
            # here things become more difficult we have to execute each of the
            # queries, but we must also hold onto cursors for each
            # then we need to link the names of the cursors that are not part
            # of the main statement to their field name
            self.main_cursor = self.interface_type()
            self.main_cursor.Connect(self.address)
            self.main_cursor.Execute(str(self.main_statement))
            self.side_cursors = {}  # key will be the side_field_name, value will
            # be the cursor holding that shit next is where we will actually
            self.side_values = {}   # this is just being initialized here
            # put the values together
            if self.side_statements:
                for statement in self.side_statements:
                    cursor = self.interface_type()
                    cursor.Connect(self.address)
                    cursor.Execute(str(statement))
                    side_field_name = statement.side_field_name
                    type = statement.side_field.type
                    self.side_cursors[side_field_name] = (cursor, type)
            # and we are all done here

    def Next(self):
        # this is going to call next on the main statement, and, if there are side
        # statements next will be called on them until the key changes and the values
        # will be recomposed from the pieces. And this will go in the side_value
        # dictionary
        self.main_cursor.Next()
        if self.side_statements:
            if not self.has_called_next:
                for field_name in self.side_cursors:
                    self.side_cursors[field_name][0].Next()    # just to get things started
            for field_name in self.side_cursors:
                (cursor, type) = self.side_cursors[field_name]
                value = self.createSideValue(field_name, cursor, type)
                self.side_values[field_name] = value

    def Get(self, field_name):
        # first we see if it is in side values:
        if field_name in self.side_values:
            return self.side_values[field_name]
        else:
            return self.main_cursor.Get(field_name)

    def createSideValue(self, field_name, cursor, type):
        # so we call cursor next repeatedly until the pk changes
        pk_value = cursor.Get(self.pk_name)
        phoenix_pieces = [cursor.Get(field_name)]
        while True:
            cursor.Next()
            new_pk_value = cursor.Get(self.pk_name)
            if new_pk_value != pk_value:
                break
            else:
                phoenix_pieces.append(cursor.Get(field_name))
        # now we can put the pieces together
        # first we convert all of the pieces from the phoenix form
        piece_type = type.piece_type
        pieces = []
        for phoenix_piece in phoenix_pieces:
            pieces.append(piece_type.TurnSolr(phoenix_piece))
        # now we recombine
        value = type.Combine(pieces)
        return value

    def Close(self):
        pass
