from xmlextractor import XMLExtractor

def expandChildren(node, number):
    to_print = '-'*number + node.name
    for key in node.attributes:
        to_print = to_print + ' ' + key + '=' + node.attributes[key]
    print(to_print)
    for child in node.children:
        expandChildren(child, number + 1)

ex = XMLExtractor()
ex.InputFile('schema.xml')
ex.CreateDocument()
for node in ex.document.nodes:
    expandChildren(node, 0)
