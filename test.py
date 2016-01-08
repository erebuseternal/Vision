from typehandler import SolrSchemaIngestor

si = SolrSchemaIngestor()
si.InputFile('schema.xml')
si.CreateDocument()
si.Process()
print(si.fieldTypes)
print(si.fields)
print(si.key)
