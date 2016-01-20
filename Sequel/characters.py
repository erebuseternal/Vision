# Python File characters.py (part of Sequel)

from copy import *

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

class Field:
    """
    This class represents a field
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

class Constraint:
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
        if isinstance(field, Field):
            self.fields.append(field)
        else:
            raise Issue("the field you tried to add isn't an instance of Field")

    def AddConstraint(self, constraint):
        if isinstance(constraint, Constraint):
            self.constraints.append(constraint)
        else:
            raise Issue("the constraint you tried to add isn't an instance of Constraint")

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
        schema_string = schema_string[1:-1]
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
then a list of upsert fields.
"""

class UpsertField:

    def __init__(self, field, value):
        if not isinstance(field, Field):
            raise Issue("the field you tried to add isn't an instance of Field")
        self.name = field.name
        self.type = field.type
        self.value = value

class Upsert(Character):
    table_name = None
    fields = [] # this is the list of upsert fields

    def SetTableName(self, table_name):
        self.table_name = table_name

    def AddField(self, field):
        if not isinstance(field, UpsertField)
            raise Issue("the field you tried to add isn't an instance of UpsertField")
        self.fields.append(field)

    def Speak(self):
        # we need to put together the field list and the value list together
        # we definitely want to do this at the same time, because the values
        # need to come in the same order as the fields come
        field_text = ''
        value_text = ''
        for field in self.fields:
            field_text = field_text + ' ' + field.name + ','
            value_text = '%s %s,' % (value_text, field.value)
        # now we need to clip the first space and last comma from each of these
        # and then we are ready to go!
        field_text = field_text[1:-1]
        value_text = value_text[1:-1]
        # ready to go! :D
        statement = 'UPSERT INTO %s(%s) VALUES (%s)' % (self.table_name, field_text, value_text)
        return statement

"""
Tables. Tables have two parts, the table name and then the table alias.
So this will be pretty simple
"""

class QueryTable:
    name = None
    alias = None

    def SetName(self, name):
        self.name = name

    def SetAlias(self, alias):
        self.alias = alias

    def RemoveAlias(self):
        self.alias = None

    def __str__(self):
        if self.alias:
            return '%s AS %s' % (self.name, self.alias)
        else:
            return self.name

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
    kind = None # the type of content
    table = None    # the table from which we get the field specified
                    # if there is one
    keywords = []
    type = None

    def SetName(self, name):
        self.name = name

    def RemoveName(self):
        self.name = None

    def SetField(self, field, as_name=True):
        # this sets the content as a field name. If as_name is true
        # it also sets name to the field_name
        if not isinstance(field, Field):
            raise Issue("the field you tried to add isn't an instance of Field")
        self.content = field.name
        self.kind = 'FIELD'
        self.type = field.type
        if as_name:
            self.name = field.name

    def SetValue(self, value, type='GenericType'):
        # this sets the content as a constant value
        self.content = value
        self.kind = 'VALUE'
        self.type = type  # just to allow queryfield converter to deal with this

    def SetFunction(self, function, argument):
        # this sets the content as a function
        if not isinstance(field, Field):
            raise Issue("the field you tried to add isn't an instance of Field")
        self.content = {'function' : function, 'argument' : field.name}
        self.type = field.type
        self.kind = 'FUNCTION'

    def SetTable(self, table):
        if isinstance(table, QueryTable):
            self.table = table
        else:
            raise Issue('the table you attempted to enter is not an instance of QueryTable')

    def AddKeyword(self, keyword):
        self.keywords.append(keyword)

    def RemoveKeyword(self, keyword):
        self.keywords.pop(keyword)

    def prepareField(self, content):
        # this puts everything around the field that's needed
        if self.table:
            if self.table.alias:
                product = '%s.%s' % (content, self.table.alias)
            else:
                product = '%s.%s' % (content, self.table.name)
        else:
            product = content
        for keyword in self.keywords:
            product = '%s %s' % (keyword, product)
        return product

    def __str__(self):
        if self.kind == 'FUNCTION':
            if self.name:
                return '%s(%s) AS %s' % (self.content['function'], self.prepareField(self.content['argument']), self.name)
            else:
                return '%s(%s)' % (self.content['function'], self.prepareField(self.content['argument']))
        elif self.kind == 'VALUE':
            if self.name:
                return '%s AS %s' % (self.content, self.name)
            else:
                return '%s' % self.content  # this is here to handle fields used
                                            # in conditions which don't need names
        elif self.kind == 'FIELD':
            if self.name == self.content:
                return self.prepareField(self.content)
            else:
                if self.name:
                    return '%s AS %s' % (self.prepareField(self.content), self.name)
                else:
                    return self.prepareField(self.content)

"""
For the where statement we have conditional statements. And we are also going
to have some grouping of those statments. So the question becomes: how do we
want to handle this?

Well for where and having we have as elements an expression that is composed
of two 'values' and a comparison operator. Now the values are either a field,
a function, or a constant value. So we can just use query fields! So we will
have two fields and an operator
"""

class QueryCondition:
    first_operand = None
    second_operand = None
    operator = None
    addition_state = 1

    def AddOperator(self, operator):
        self.operator = operator

    def AddOperand(self, operand1, operand2=None):
        if not isinstance(operand1, QueryField):
            raise Issue('first operand entered is not of type QueryField')
        # now we quickly remove the name of the operand1 (if it has one)
        operand1 = deepcopy(operand1)
        operand1.RemoveName()
        if operand2 == None:
            if self.addition_state == 1:
                self.first_operand = operand1
                self.addition_state = 2
            else:
                self.second_operand = operand1
                self.addition_state = 1
        else:
            if not isinstance(operand2, QueryField):
                raise Issue('second operand entered is not of type QueryField')
            # remove name from operand2
            operand2 = deepcopy(operand2)
            operand2.RemoveName()
            self.first_operand = operand1
            self.second_operand = operand2
            self.addition_state = 1

    def AddFirstOperand(self, operand):
        self.first_operand = operand
        self.addition_state = 2

    def AddSecondOperand(self, operand):
        self.second_operand = operand
        self.addition_state = 1

    def __str__(self):
        return '%s %s %s' % (self.first_operand, self.operator, self.second_operand)

"""
Finally, just to keep things pretty, we need to handle order by fields.
These are simply query fields and then an optional keyword
"""

class QueryOrder:
    field = None
    keyword = None

    def SetKeyword(self, keyword):
        self.keyword = keyword

    def RemoveKeyword(self):
        self.keyword = None

    def SetField(self, field):
        if not isinstance(field, QueryField):
            raise Issue('field entered is not an instance of QueryField')
        self.field = field

    def __str__(self):
        if self.field.name: # if there is a name we want to use it
            if self.keyword:
                return '%s %s' % (self.field.name, self.keyword)
            else:
                return self.field.name
        else:   # otherwise we want the print like it would be in a conditional statement
            if self.keyword:
                return '%s %s' % (self.field, self.keyword)
            else:
                return '%s' % self.field

"""
So we are now ready to put write the select statement object! Remembering from
above:

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

So we will have a fields list, a table list, a groupby list and an order by list.
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
    parent = None
    children = []
    sibling = None # assumed to be the next sibling
    operator = None
    condition = None

    def SetCondition(self, condition):
        if not isinstance(condition, QueryCondition) and condition:
            raise Issue('entered condition is not an instance of QueryCondition and is not None')
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

class Select(Character):
    fields = []
    tables = []
    orderby = []
    groupby = []
    where = None
    last_added_where_node = None
    having = None
    last_added_having_node = None
    where_group_entry = False
    having_group_entry = False

    def AddField(self, field):
        if not isinstance(field, QueryField):
            raise Issue('entered field is not an instance of QueryField')
        self.fields.append(field)

    def AddTable(self, table):
        if not isinstance(table, QueryTable):
            raise Issue('entered table is not an instance of QueryTable')
        self.tables.append(table)

    def AddGroupingField(self, field):
        if not isinstance(table, QueryField):
            raise Issue('entered field is not an instance of QueryField')
        # have to get rid of the name if there is one
        field.RemoveName()
        self.groupby.append(field)

    def AddOrderBy(self, orderby):
        if not isinstance(orderby, QueryOrder):
            raise Issue('entered orderby is not an instance of QueryOrder')
        self.orderby.append(orderby)

    def AddWhereCondition(self, condition, operator='AND'):
        # operator is only used once at least one condition is present in the where
        # and gets attached to the last added condition
        if not self.where:
            new_node = Node()
            new_node.SetCondition(condition)
            self.where = new_node
            self.last_added_where_node = new_node
        else:
            if self.last_added_where_node.condition:
                # create a sibling for the last node
                new_node = self.last_added_where_node.CreateSibling()
            else:   # this is the case where the last one created was a group
                    # or we just exited a group
                if self.where_group_entry:
                    # just entered a group
                    new_node = self.last_added_where_node.CreateChild()
                else:
                    # just exited
                    new_node = self.last_added_where_node.CreateSibling()
            # set the nodes condition
            new_node.SetCondition(condition)
            # set the operator on the last condition
            self.last_added_where_node.SetOperator(operator)
            self.last_added_where_node = new_node


    def AddWhereGroup(self, operator='AND'):
        self.AddWhereCondition(None, operator)
        self.where_group_entry = True

    def ExitWhereGroup(self):
        # all we have to do is go back up a level
        self.last_added_where_node = self.last_added_where_node.parent
        self.where_group_entry = False

    def AddHavingCondition(self, condition, operator='AND'):
        # operator is only used once at least one condition is present in the where
        # and gets attached to the last added condition
        if not self.having:
            new_node = Node()
            new_node.SetCondition(condition)
            self.having = new_node
            self.last_added_having_node = new_node
        else:
            if self.last_added_having_node.condition:
                # create a sibling for the last node
                new_node = self.last_added_having_node.CreateSibling()
            else:   # this is the case where the last one created was a group
                    # or we just exited a group
                if self.having_group_entry:
                    # just entered a group
                    new_node = self.last_added_having_node.CreateChild()
                else:
                    # just exited
                    new_node = self.last_added_having_node.CreateSibling()
            # set the nodes condition
            new_node.SetCondition(condition)
            # set the operator on the last condition
            self.last_added_having_node.SetOperator(operator)
            self.last_added_having_node = new_node


    def AddHavingGroup(self, operator='AND'):
        self.AddHavingCondition(None, operator)
        self.having_group_entry = True

    def ExitHavingGroup(self):
        self.last_added_having_node = self.last_added_having_node.parent
        self.having_group_entry = False

    def Speak(self):
        # first we start with the fields
        select_text = 'SELECT'
        for field in self.fields:
            select_text = '%s %s,' % (select_text, field)
        select_text = select_text[:-1]  # shave off last comma
        # next we do tables
        from_text = '\nFROM'
        for table in self.tables:
            from_text = '%s %s,' % (from_text, table)
        from_text = from_text[:-1]
        # next we handle the where clause
        where_text = ''
        if self.where:
            where_text = '\nWHERE %s' % (self.where)  # invoking that cool string generation
                                                    # method for nodes
        # next we handle the groupby clause
        groupby_text = ''
        if len(self.groupby) > 0:
            groupby_text = '\nGROUPBY'
            for field in self.groupby:
                groupby_text = '%s %s,' % (groupby_text, field)
            groupby_text = groupby_text[:-1]
        # next having
        having_text = ''
        if self.having:
            having_text = '\nHAVING %s' % self.having
        # finally orderby
        orderby_text = ''
        if len(self.orderby) > 0:
            orderby_text = '\nORDERBY'
            for field in self.orderby:
                orderby_text = '%s %s,' % (orderby_text, field)
            orderby_text = orderby_text[:-1]
        # and now we put it all together
        return select_text + from_text + where_text + groupby_text + having_text + orderby_text

"""
And now for delete
"""

class Delete(Character):
    table_name = None
    where = None
    last_added_where_node = None
    where_group_entry = False

    def SetTableName(self, table_name):
        self.table_name = table_name

    def AddWhereCondition(self, condition, operator='AND'):
        # operator is only used once at least one condition is present in the where
        # and gets attached to the last added condition
        if not self.where:
            new_node = Node()
            new_node.SetCondition(condition)
            self.where = new_node
            self.last_added_where_node = new_node
        else:
            if self.last_added_where_node.condition:
                # create a sibling for the last node
                new_node = self.last_added_where_node.CreateSibling()
            else:   # this is the case where the last one created was a group
                    # or we just exited a group
                if self.where_group_entry:
                    # just entered a group
                    new_node = self.last_added_where_node.CreateChild()
                else:
                    # just exited
                    new_node = self.last_added_where_node.CreateSibling()
            # set the nodes condition
            new_node.SetCondition(condition)
            # set the operator on the last condition
            self.last_added_where_node.SetOperator(operator)
            self.last_added_where_node = new_node


    def AddWhereGroup(self, operator='AND'):
        self.AddWhereCondition(None, operator)
        self.where_group_entry = True

    def ExitWhereGroup(self):
        # all we have to do is go back up a level
        self.last_added_where_node = self.last_added_where_node.parent
        self.where_group_entry = False

    def Speak(self):
        if self.where:
            return 'DELETE FROM %s WHERE %s' % (self.table_name, self.where)
        else:
            return 'DELETE FROM %s' % self.table_name
