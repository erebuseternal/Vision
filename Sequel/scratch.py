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

class Type:
    solr = 'GenericType'
    phoenix = 'GenericType'
    separate_table = False  # this indicates whether a separate table is needed
                            # for this type
    value_type = None

    def TurnPhoenix(self, solr_value):
        # override this
        return solr_value

    def TurnSolr(self, phoenix_value):
        # override this
        return phoenix_value

class SideType(Type):
    separate_table = True
    value_type = Type()

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
    value_type = String()

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

    def __str__(self):
        # these are here so that only writing out the SQL statement
        # and not each of the statements individual pieces with all of
        # their details matters
        if self.is_pk:
            return '%s %s PRIMARY KEY' % (self.name, self.type.phoenix)
        else:
            return '%s %s' % (self.name, self.type.phoenix)

class Table:
    """
    This class represents a table, and a table is really just a
    schema object
    """

    def __init__(self, name):
        self.name = name
        self.fields = {}
        self.has_pk = False
        self.pk = None

    def AddField(self, field):
        checkType(field, Field)
        # first we check to see if we are adding a field with a name already
        # used by another field
        if field.name in self.field_dictionary:
            raise Issue('Field name already taken')
        # next we check to see if we are trying to add a primary key
        if field.is_pk:
            # if we already have one, then we raise an Issue
            if self.has_pk:
                raise Issue('Trying to add a redundant Primary Key')
            else:
                self.fields[field.name] = field
                # and we let the object know it has a primary key
                self.has_pk = True
                self.pk = field
        else:
            self.fields[field.name] = field

    # this returns a new table with the field removed
    def RemoveField(self, field_name):
        if not field_name in self.fields:
            raise Issue('Attempted to remove a non-existant field')
        else:
            new_table = deepcopy(self)
            del new_table.fields[field_name]
            return new_table

    def GetFields(self):
        return self.fields

    def Split(self):
        # this returns a set of tables split by fields needing separate tables
        tables = [self]
        fields = self.GetFields()
        for field_name in fields:
            field = fields[field_name]
            if field.type.separate_table:
                # first we create a table with the removed field
                tables[0] = tables[0].RemoveField(field_name)
                # then we create a sidetable
                tables.append(SideTable(self, field))
        return tables

class SideTable(Table):

    def __init__(self, side_field, table):
        checkType(table, Table)
        Table.__init__(self, table.name)
        checkType(side_field, Field)
        if not table.has_pk:
            raise Issue('Input table has no primary key')
        # now we create our fields
        pk = table.pk
        position = Field('position', Int())
        value = Field('value', side_field.type.value_type)
        self.AddField(pk)
        self.AddField(position)
        self.AddField(value)
        self.side_field = side_field    # for reference


class SingleTableCharacter:

    def __init__(self, table):
        checkType(table, Table)
        if not table.has_pk:
            raise Issue('Input table has no primary key')
        self.table = table

"""
So now we can immediately make a Create statement object
"""

class Create(SingleTableCharacter):

    def Split(self):
        # this will split the table on the fields that need separate
        # tables and then go ahead and make creates for each of these
        tables = self.table.Split()
        # now we create a list of creates based off of this
        creates = []
        for table in tables:
            create = Create(table)
            creates.append(create)
        return creates


    def Speak(self):
        # so first we make the schema part of things
        schema_string = ''
        fields = self.table.GetFields()
        for field_name in fields:
            schema_string = '%s%s, ' % (schema_string, fields[field_name])
        # we cut off the last comma and space
        schema_string = schema_string[:-2]
        # and now we put everything together
        line = 'CREATE TABLE %s (%s)' % (self.table.name, schema_string)
        return line

"""
Next, for upserts and conditions, we are going to need a value class.
We are going to have the values take a type, so that we can ensure the
person is paying attention to what types they are inputting and all of that jazz.
Remember a value is more than just its representation

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
    def __str__(self):
        # here we just need to convert the solr representation and print that
        phoenix_representation = self.type.TurnPhoenix(self.representation)
        return str(phoenix_representation)

class Upload(SingleTableCharacter):

    def __init__(self, table):
        SingleTableCharacter.__init__(self, table)
        self.values = {}    # keys should be field names, and values Value objects

    def Split(self):
        """
        1. Split table
        2. Isolate the main table
        3. Add all of the values to the main table in its own upload statement
        3. Pair up the remaining tables and the values associated with them
        4. Break the value based on its type
        5. Create uploads for every part of the value and do this for each
            side table using the pk
        6. return them uploads
        """
        tables = self.table.Split()
        main_table = tables[0]
        fields = main_table.GetFields()
        main_upload = Upload(main_table)
        for field_name in fields:
            main_upload.SetValue(field_name, self.values[field_name])
        uploads = [main_upload]
        side_tables = tables[1:]
        pk_name = self.table.pk.name
        pk_value = self.values[pk_name]
        for table in side_tables:
            field_name = table.side_field.name
            value = self.values[field_name]
            pieces = self.value.type.Break(value)
            position = 0
            for piece in pieces:
                upload = Upload(table)
                position_value = Value(position, Int())
                upload.SetValue(pk_name, pk_value)
                upload.SetValue('position', position_value)
                upload.SetValue(field_name, piece)
                position = position + 1
                uploads.append(upload)
        return uploads


    def SetValue(self, field_name, value):
        checkType(value, Value)
        # next we check to make sure the field name is valid
        fields = self.table.GetFields()
        if not field_name in fields:
            raise Issue('Setting value to a non-existant field')
        if not fields[field_name].type == value.type:
            raise Issue('Value and field have inconsistent types')
        # so we know that we are okay and we go ahead and add the value
        self.values[field_name] = value

    def Speak(self):
        # first we check that all fields have been set
        fields = self.table.GetFields()
        for field_name in fields:
            if not field_name in self.values:
                raise Issue('Value missing for at least field: %s' % field_name)
        # so know that we know we are good, we go ahead and create the value string
        # and the field string at the same time
        field_string = ''
        value_string = ''
        for field_name in fields:
            field_string = '%s%s, ' % (field_string, field_name)
            value_string = '%s%s, ' % (value_string, self.values[field_name])
        # now we cut off the extra comma and space from both
        field_string = field_string[:-2]
        value_string = value_string[:-2]
        # and now we can create our line
        line = 'UPSERT INTO %s(%s) VALUES (%s)' % (self.table.name, field_string, value_string)
        return line



"""
The next few classes depend upon a where clause. This requires us to have some notion
of conditions. Note that I am assuming that we do not do groupings or analysis type
actions on the data in our statements. This is because not all of them can be used as
such, and so for consistency, if you want to use such functionality, you need to
go to a lower level
"""

class Condition:

    def __init__(self):
        self.first_operand = None
        self.second_operand = None
        self.operator = None

    def AddOperator(self, operator):
        self.operator = operator

    def AddFirstOperand(self, operand):
        checkType(operand, Field)
        self.first_operand = operand

    def AddSecondOperand(self, operand):
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

class WhereCharacter(SingleTableCharacter):

    def __init__(self, table):
        SingleTableCharacter.__init__(self, table)
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
            if not second_operand in fields:
                raise Issue('Second Operand was a string but was not found in the table as a field')
            operand2 = fields[second_operand]
        elif isinstance(second_operand, Value):
            if not operand1.type == second_operand.type:
                raise Issue('input field and value are of inconsistent types')
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

# this class if for finding a key based on a where statement
class KeyFinderQuery:

    # we initialize with a statement
    def __init__(self, statement):
        checkType(statement, WhereCharacter)
        self.table = statement.table
        self.where = statement.where
        self.pk = self.table.pk

    def __str__(self):
        if self.where:
            line = 'SELECT %s FROM %s WHERE %s' % (self.pk.name, self.table.name, self.where)
        else:
            line = 'SELECT %s FROM %s' % (self.pk.name, self.table.name)
        return line

class KeyBasedStatement:

    def __init__(self, type, side_table, key_finder):
        checkType(side_table, SideTable)
        checkType(key_finder, KeyFinderQuery)
        checkType(original_statment, WhereCharacter)
        self.key_finder = key_finder
        self.side_table = side_table
        self.type = type
        self.pk = side_table.pk

    def __str__(self):
        if self.type == Delete:
            return 'DELETE FROM %s WHERE %s IN (%s)' % (self.side_table.name, self.pk, self.key_finder)
        if self.type == Select:
            return 'SELECT value FROM %s WHERE %s IN (%s) ORDERBY position ASC' % (self.side_table.name, self.pk, self.key_finder)

class CompleteStatment(WhereCharacter):

    def __init__(self, table):
        WhereCharacter.__init__(self, table)
        self.fields = {}

    def AddField(self, field_name):
        fields = self.table.GetFields()
        if not field_name in fields:
            raise Issue('Trying to use a non existant field')
        self.fields[field_name] = fields[field_name]

    def Split(self):
        tables = self.table.Split()
        type = type(self)
        main_table = tables[0]
        side_tables = tables[1:]
        main_statement = type(main_table)
        fields = main_table.GetFields()
        for field_name in fields:
            if field_name in self.fields:
                main_statement.AddField(field_name)
        statements = [main_statement]
        key_finder = self.GenerateKeyFinder()
        for table in side_tables:
            statement = KeyBasedStatement(type, table, key_finder)
            statements.append(statement)
        return statements

class Select(CompleteStatment):

    def __str__(self):
        field_string = ''
        for field_name in self.fields:
            field_string = '%s%s, ' % (field_string, field_name)
        field_string = field_string[:-2]
        if self.where:
            line = 'SELECT %s FROM %s WHERE %s' % (field_string, self.table.name, self.where)
        else:
            line = 'SELECT %s FROM %s' % (field_string, self.table.name)

class Delete(CompleteStatment)

    def __str__(self):
        field_string = ''
        for field_name in self.fields:
            field_string = '%s%s, ' % (field_string, field_name)
        field_string = field_string[:-2]
        if self.where:
            line = 'DELETE FROM %s WHERE %s' % (field_string, self.table.name, self.where)
        else:
            line = 'DELETE FROM %s' % (field_string, self.table.name)
