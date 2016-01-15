from fieldextractor import *

fieldextractor = FieldExtractor('')
fieldextractor.InputFile('SolrData/Bear')
fieldextractor.ExtractFields()
fieldtracker = FieldTracker()
fieldtracker.InputFile('page.html')
fieldtracker.Process()
print joinData(fieldextractor, fieldtracker)
