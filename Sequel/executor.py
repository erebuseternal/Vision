# Python File executor.py

"""
SQL statements are essentially statements of intent. Something else actually
parses out and executes them. And as far as the execution of SQL statement
objects written in solr schema are concerned, the Executor is here! The Executor
stands as an interface between SQL statement objects and a phoneix interface
(which is just a convenient mask for a cursor)
"""

"""
This class needs two things, an execute method which executes a SQL statement
(in phoneix speak) and returns a status of operation indicator (true or false)
and __getitem__ to pull the corresponding attribute from the cursor
"""

from translator import *

class Interface:

    def Execute(self, SQL_object):
        # this should have the sql object speak and then execute it
        # using a cursor of some kind
        # then it needs to return true if the operation was a success
        # and false if it failed
        return True

    def NextValue(self):
        # should return none when there are no more values
        pass

    def __getitem__(self, key):
        # should overide this in order to get the data from the cursor
        pass

"""
The Executor class takes in an SQL_object (solr-wise) converts it and then
handles the resulting SQL objects
"""

class Executor:

    key = None

    def __init__(self, interface):
        self.interface = interface

    def AddKeyField(self, key):
        self.key = key

    def Execute(self, SQL_object):

    def ExecuteCreate(self, SQL_object, key=self.key):
        creates = translateCreate(SQL_object, key)
        for create in creates:
            if not self.interface.Execute(create):
                raise Issue('create %s was a problem to execute' % create.Speak())

    def ExecuteUpsert(self, SQL_object, key=self.key):
        upserts = translateCreate(SQL_object, key)
        for upsert in upserts:
            if not self.interface.Execute(upsert):
                raise Issue('upsert %s was a problem to execute' % upsert.Speak())

    def ExecuteDelete(self, SQL_object, key=self.key):
        deletes = []
        find_key = None
        filtered_fields = []
        base_delete = Delete()
        base_delete.SetTable(SQL_object.table_name)
        # first we go through and convert delete and filter out the fields for
        # special deletion
        for field in SQL_object.fields:
            if (new_field = queryFieldConverter(field)):
                base_delete.AddField(new_field)
            else:
                filter_fields.append(field)
        # next we get the keys that match the condition
        key_select = getKeySelect(key, SQL_object, False)
        self.interface.Execute(key_select)
        keys = []
        while self.interface.NextValue():
            keys.append(self.interface[key.name])
        # now we go through and create the new delete statements
        for field in fields:
            delete = 
