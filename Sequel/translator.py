# Python File translator.py

"""
This python file will contain all of the info for converting a SQL statement
object created from solr schema into a set of SQL statements in phoenix speak
"""

"""
NOTE!!!!! Typing code that is the basis of conversion should notice when something
is already in the form needed, and then just keeps it that way.
"""

from characters import *
from copy import *

class Type:
    solr = 'GenericType'
    phoenix = 'GenericType'
    separate_table = False  # this indicates whether a separate table is needed
                            # for this type

    def TurnPhoenix(self, solr_value):
        # override this
        return solr_value

    def TurnSolr(self, phoenix_value):
        # override this
        return phoenix_value

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

class Text(Type):
    solr = 'Text'
    phoenix = 'VARCHAR'
    separate_table = True

    def TurnPhoenix(self, solr_value):
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

    def TurnSolr(self, phoenix_value):
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

def fieldConverter(field, is_solr=True):
    # this will return a schema field with the right type given the conversion if
    # there is no need for a new table. If there is it returns None
    typer = Typer()
    type = typer.Type(field.type, is_solr)
    if not type.separate_table:
        field = deepcopy(field)
        if is_solr:
            field.type = type.phoenix
        else:
            field.type = type.solr
        return field
    else:
        return None

def upsertFieldConverter(upsert_field, is_solr=True):
    typer = Typer()
    type = typer.Type(upsert_field, is_solr)
    if not type.seperate_table:
        upsert_field = deepcopy(upsert_field)
        if is_solr:
            upsert_field.type = type.phoenix
        else:
            upsert_field.type = type.solr
        if is_solr:
            upsert_field.value = type.TurnPhoenix(upsert_field.value)
        else:
            upsert_field.value = type.TurnSolr(upsert_field.value)
        return upsert_field
    else:
        return None

def queryFieldConverter(query_field, is_solr=True):
    typer = Typer()
    type = typer.Type(query_field.type, is_solr)
    if not type.separate_table:
        query_field = deepcopy(query_field)
        if is_solr:
            query_field.type = type.phoenix
        else:
            query_field.type = type.solr
        # if it is a value we want to convert the value before returning it
        if query_field.kind == 'VALUE':
            if is_solr:
                query_field.content = type.TurnPhoenix(query_field.content)
            else:
                query_field.content = type.TurnSolr(query_field.content)
        return query_field
    else:
        return None

def queryConditionConverter(condition, is_solr=True):
    # So we have two cases to deal with. One is where one of the conditions
    # has a separate_table type. The other is where we have one field and then
    # a value, in which case we need to transform the value
    if condition == None:
        return condition    # note that a group node looks like a node that couldn't get processed
    operand1 = condition.first_operand
    operand2 = condition.second_operand
    typer = Typer()
    type1 = typer.Type(operand1.type)
    type2 = typer.Type(operand2.type)
    if type1.seperate_table or type2.separate_table:
        return None # this signals as with all the converters this needs to
                    # get handled differently
    operand2 = deepcopy(operand2)
    operand1 = deepcopy(operand1)
    if is_solr:
        operand1.type = type.phoenix
        operand2.type = type.phoenix
    else:
        operand1.type = type.solr
        operand2.type = type.solr
    # next we assume in our condition a field or function comes first and then
    # a value
    if operand2.kind == 'VALUE':
        # Now we convert the value (based on the field not the type in the value)
        if is_solr:
            operand2.content = type1.TurnPhoenix(operand2.content)
        else:
            operand2.content = type1.TurnPhoenix(operand2.content)
    new_condition = QueryCondition()
    new_condition.AddOperand(operand1, operand2)
    new_condition.AddOperator(condition.operator)
    return new_condition

# now the next question is what kind of fields are going to be turned into
# additional tables. Of course fields (used in create table statements) will
# be turned into additional create table statements.
# Then in upsert statements we have to grab the primary key
# In delete statements and in select statements we have to conduct two
# statements. The first is to find the primary keys that satisfy the conditions
# given in the where or having clauses. Then we use these on the table
# the separate table field belongs too. (and we do it for each key)

# first the create table one
def fieldToCreate(self, field, key_field):
    # it is assumed you are only doing this because you are going to access
    # solr, so field_conversion happens here as well
    # this will create a table of the form:
    # name = field.name, schema, key_field, id INTEGER, val field.type
    # with name and id together being the primary key.
    create = Create()
    create.SetTableName(field.name)
    key_field = deepcopy(key_field)
    typer = Typer()
    key_type = typer.Type(key_field.type)
    key_field.type = key_type.phoenix
    id_field = Field('id', 'INTEGER')
    val_field = Field('val', typer.Type(field.type).phoenix)
    create.AddField(key_type)
    create.AddField(id_type)
    create.AddField(val_field)
    constraint = Constraint('%s_pk' % field.name, 'PRIMARY KEY(%s, %s)' % (key_field.name, 'id'))
    create.AddConstraint(constraint)
    return create

def upsertFieldToUpsert(self, upsert_field, key_field):
    # this takes two upsert fields, the field that needs a separate table, and
    # a field that is the key of this entry. It will then convert the value
    # which should return an array, and go through and add to a table of the
    # form given in fieldToCreate. Then it will return the upserts needed to do this
    upsert_array = []
    typer = Typer()
    field_type = typer.Type(upsert_field.type)
    # get our arry of values to add
    vals = field_type.TurnPhoenix(upsert_field.value)
    # deal with converting the key
    key_type = typer.Type(key_field.type)
    key_field = deepcopy(key_field)
    key_field.value = key_type.TurnPhoenix(key_field.value)
    key_field.type = key_type.TurnPhoenix(key_field.type)
    # now we get the type for val
    val_type = field_type.phoenix
    # now we get the table name
    table_name = upsert_field.name
    # now we loop through all our vals and make an upsert statement for each
    count = 0
    for val in vals:
        # create fields
        val_field = UpsertField(Field('val', field_type), val)
        id_field = UpsertField(Field('id', 'INTEGER'), count)
        # create upsert
        upsert = Upsert()
        upsert.SetTableName(table_name)
        upsert.AddField(key_field)
        upsert.AddField(id_field)
        upsert.AddField(val_field)
        # add the upsert to the upsert array
        uperst_array.append(upsert)
        count = count + 1
    # and now we can just return the array
    return upsert_array

# now, select queries to these additional table things are rather weird.
# we have to do the following in order:
#   * select key values that correspond to condition statements in the select
#   * generate a query that will return these values
#   * segment the data based on key
# in other words, our set of queries now has to be one for the first steps
# several built off of the next step (one for each value) so that we can segment
# the data at the same time. So let's start with that key retrieval

# a function we are going to need for this
def convertConditions(where, is_solr=True):
    # note that a having can go where where is equally well
    # we are going to work through this recurisive like a condition
    # node's str method works. Assumes you start on the first node
    # you are interested in and return a new node (with children
    # and siblings and all) from there
    if where:
        node = deepcopy(where)
        nodeconvert(node, is_solr)
        return node

def nodeconvert(node, is_solr=True):
    # convert the node at hand and call on sibling (if there is one) and
    # on children if there are any
    if node.condition:
        node.condition = queryConditionConverter(node.condition, is_solr)
    else:
        nodeconvert(node.children[0], is_solr)
    nodeconvert(node.sibling, is_solr)

# okay now to get the key values given a select statement
def getKeySelect(key_field, statement, is_select=True):
    # this will return a select statement that will get us our keys
    # first we have to convert the where and having to phoenix versions
    # i.e. at least make sure they are in that form
    if is_select:
        key_statement = Select()
    else:
        key_statement = Delete()
    key_statement.fields = []
    key_statement.SetTable(deepcopy(statement.table))
    key_statement.AddField(key_field)
    key_statement.where = convertConditions(statement.where)
    if is_select:
        key_statement.having = convertConditions(statement.having)
        key_statement.groupby = deepcopy(statement.groupby)
        key_statement.orderby = deepcopy(statement.orderby)
    return key_statement

# next we are going to use a key value to get create a select statement for
# a separate table field
def getSeparateTableSelect(query_field, key_field, key_value):
    select = Select()
    # set up the orderby
    id_field = QueryField()
    id_field.SetField(Field('id', 'INTEGER'))
    orderby = OrderBy()
    orderby.SetKeyWord('ASC')
    orderby.SetField(id_field)
    # set up the field we will be selecting
    typer = Typer()
    type = typer.Type(query_field)
    # val field
    val_field = QueryField()
    val_field.SetField(Field('val'), type.phoneix)
    # set up the condition
    key_field = queryFieldConverter(key_field)  # just to be sure and consistent
    # key value will have come from a converted select statement so it is already
    # the right value but it should be in queryfield form so that it can go
    # into a condition
    condition = QueryCondition()
    condition.AddOperand(key_field, key_value)
    condition.SetOperator('=')
    # set up the table
    table = QueryTable().SetName(query_field.name)
    # set up the select
    select.AddTable(table)
    select.AddField(val_field)
    select.AddWhereCondition(condition)
    # finally we need to order by id
    select.AddOrderBy(orderby)
    return select

def getSeparateTableDelete(query_field, key_field, key_values):
    delete = Delete()
    delete.SetTable(query_field.name)
    key_field = queryFieldConverter(key_field)
    for key in key_values:
        condition = QueryCondition()
        condition.AddOperand(key_field, QueryField().SetValue(key, key_field.type))
        condition.AddOperator('=')
        delete.AddWhereCondition(condition, 'OR')


"""
Note that when we query data we are querying from one base table and one
base table only. This is because that's how solr works, one index at a time.
Also it keeps from a lot of confusion and mayhem
"""

def translateCreate(create, key_field):
    # we are going to go through each field and keep and convert the ones that
    # don't need a new table, and create create statements for those that do
    creates = []
    base_create = Create()
    creates.append(base_create)
    base_create.SetTableName(create.table_name)
    base_create.constraints = deepcopy(create.constraints)
    for field in create.fields:
        if (new_field = fieldConverter(field)):
            base_create.AddField(new_field)
        else:
            creates.append(fieldToCreate(field, key_field))
    return creates

def translateUpsert(upsert, key_field):
    upserts = []
    base_upsert = Upsert()
    upserts.append(base_upsert)
    base_upsert.SetTableName(upsert.table_name)
    for field in upsert.fields:
        if (new_field = upsertFieldConverter(field)):
            base_upsert.AddField(new_field)
        else:
            upserts.extend(upsertFieldToUpsert(field, key_field))
    return upserts
