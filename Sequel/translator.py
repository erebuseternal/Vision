# Python File translator.py

"""
This python file will contain all of the info for converting a SQL statement
object created from solr schema into a set of SQL statements in phoenix speak
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
        date = solr_value[:10] # cutting off T at end of date in solr value
        time = solr_value[11:-1] # cutting off Z at end of solr value
        value = date + ' ' + time
        return value

    def TurnSolr(self, phoenix_value):
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
    types = [Bool(), Date(), String(), Text(), Double(), Int(), Float(), Long()]

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

def SchemaFieldConverter(schema_field, is_solr=True):
    # this will return a schema field with the right type given the conversion if
    # there is no need for a new table. If there is it returns None
    typer = Typer()
    type = typer.Type(schema_field.type, is_solr)
    if not type.separate_table:
        schema_field = deepcopy(schema_field)
        schema_field.type = type
        return schema_field
    else:
        return None

def UpsertFieldConverter(upsert_field, is_solr=True):
    typer = Typer()
    type = typer.Type(upsert_field, is_solr)
    if not type.seperate_table:
        upsert_field = deepcopy(upsert_field)
        upsert_field.type = type
        if is_solr:
            upsert_field.value = type.TurnPhoenix(upsert_field.value)
        else:
            upsert_field.value = type.TurnSolr(upsert_field.value)
        return upsert_field
    else:
        return None
