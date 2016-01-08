#Python File markupcreator.py

"""
This file contains the objects that I will use to ease the creation
of markup files. By markup files I mean files composed of 'nodes' of
the following form:
<tagname key1="value1" key2="value2" ...> content
<child1 ...>...</child1>
<child2 ...>...</child2>
...
</tagname>
"""

class DocumentNode:
    """
    This will be a document node object which has a name, attributes, content and the
    potential for children, a parent, and an older and younger sibling (so we can keep)
	track of sibling order for exporting nodes to a document
    """

    def __init__(self, name):
        self.parent = None
        self.children = []
        self.older_sibling = None
        self.younger_sibling = None
        self.name = name
        self.content = None
        self.attributes = {}

    def AddChild(self, child):
        # sets appropriate things for both parent and child
        self.children.append(child)
        child.parent = self

    def AddYoungerSibling(self, sibling):
        # sets appropriate things for both siblings
        self.younger_sibling = sibling
        sibling.older_sibling = self

class StructuredDocument:
    """
    This is an object designed for easy creation and exporting
    of structured markup languages.

    CREATION:
    We can create, add content, and the finish nodes. The content creation
    is optional, but the first and last must follow in order, or the object
    will ignore you when you try something else. Then, while finishing a node
    you can freeze it as a parent in order to create children for it. You can
    do this while finishing any node. As you add children, the order of those
    children will be remembered and used when exporting the document. Once
    you are done creating children you can simply start creating nodes again, or
    if you would like to go back to a parent, grandparent, etc. you can call
    FinishChildren to go back up to the parent of your current parent and
    continue adding children as normal. (You can call it repeatedly).

    Finally the various root nodes get added to a node list to keep track of them

    Therefore you must work depth first in creating these structured pages
    """

    def __init__(self, directory):
        self.directory = directory
        self.nodes = []
        self.current_node = None
        self.current_parent = None
        self.last_sibling = None

    # CREATION -----------------------------------------------------------------

    def ReadyForAction(self):
        # returns true if current_action is None
        # returns false and sends a message other wise
        # used to prevent us from creating nodes before
        # others are done
        if self.current_node:
            print "Skipping node creation, node: %s already in creation" % self.current_node.name
            return False
        else:
            return True

    def CreateNode(self, node_name):
        # we will create a node with the appropriate node_name
        if self.ReadyForAction():
            self.current_node = DocumentNode(node_name)

    def AddContent(self, content):
        # this will add content to the current node
        if self.current_node:
            self.current_node.content = content
        else:
            print "No node in process of creation, skipping content addition"

    def AddAttributes(self, **attributes):
        # This will take an arbitrary number of key value pairs (arguments)
        # and add them as attributes (key-value pairs)
        if self.current_node:
            for key in attributes:
                self.current_node.attributes[key] = attributes[key]
        else:
            print "No node in process of creation, skipping attributes addition"

    def FinishNode(self, freeze_as_parent=False):
        # this will add the node to our node list if it is not a child
        # and reset current_node
        # but it will first check to see if we want to keep track of it in
        # order to add children (if so we will set it as parent and set last)
        # sibling to None (just to be sure things work right)
        if self.current_node:
            if not self.current_node.parent:
                self.nodes.append(self.current_node)
            if freeze_as_parent == True:
                self.current_parent = self.current_node
                self.last_sibling = None # no children yet, so no siblings
                                        # for those children
            else:
                # in this case we must set it as the last sibling
                # in case children are being created
                self.last_sibling = self.current_node
            self.current_node = None
        else:
            print "No node in process of creation, skipping node finishing"

    def CreateChild(self, node_name):
        # if there is a current parent and we are ready for action
        # this will create a child for that parent.
        # if last_sibling exists will set up the sibling relationship as well
        if self.current_parent:
            if self.ReadyForAction():
                self.current_node = DocumentNode(node_name)
                self.current_parent.AddChild(self.current_node)
                if self.last_sibling:
                    self.last_sibling.AddYoungerSibling(self.current_node)
        else:
            print 'No parent set, skipping child creation'

    def FinishChildren(self):
        # this method tells us we are done with the children
        # for a specific node. Now there may be a case where we
        # stepped into a child that was created to create its children
        # and now want to step back. So this is going to step back for us
        # and set both current_parent and last_sibling
        if self.current_node:
            print 'Node creation in progress, skipping children finishing'
        else:
            self.current_parent = self.current_parent.parent
            if self.current_parent:
                last_sibling = self.current_parent.children[-1]
                # and the following for safety's sake we will descend
                # through all of the younger siblings if they exist
                while last_sibling.younger_sibling:
                    last_sibling = last_sibling.younger_sibling
                self.last_sibling = last_sibling
            else:
                self.last_sibling = None

    # EXPORT -------------------------------------------------------------------

    def CreateExport(self):
        # this will run through the various nodes (in order) and export each
        # with its children
        export = ''
        for node in self.nodes:
            export = export + self.CreateNodeExport(node)
        return export

    def CreateNodeExport(self, node):
        # this will first call itself on all of the nodes children, then will
        # put markup tags with the node name in those tags around the node
        # content and the results of its children's export
        children_export = ''
        if len(node.children) > 0:
            for child in node.children:
                children_export = children_export + self.CreateNodeExport(child)

        # next we need to get the string of attributes in the form key="value"
        attributes_export = ''
        for key in node.attributes:
            attributes_export = attributes_export + ' ' + writeValue(key) + '="' + writeValue(node.attributes[key]) + '"'
		# now we put everything together
        if children_export == '':
            export = '<' + node.name + attributes_export + '>' + writeValue(node.content) + '</' + node.name + '>\n'
        else:
            export = '<' + node.name + attributes_export + '>' + '\n' + writeValue(node.content) + '\n' + children_export + '</' + node.name + '>\n'
        return export

    def Export(self, file_name):
        # this simply exports into the directory initially specified in __init__
        # into a file named through a passed argument
        export = self.CreateExport().encode('utf-8')
        file = open(self.directory + '/' + file_name, 'wb')
        file.write(export)
        file.close()

    # END ----------------------------------------------------------------------

def writeValue(value):
	# this just keeps us from writing None when our value doesn't exist
	if value:
		return '%s' % value
	else:
		return ''

class HTMLExtractor:
    """
    This class will be used to extract the various bits and pieces we might
    want from an HTML document that has been grabbed through BeautifulSoup
    essentially it will allow you to grab a specific set of tags with pertinant
    attributes and be able to extract their children in such a way that you
    can extract what it is you want for your data.

    We will of course be extracting the data into a structured document

    The way it works is the following. We create representive nodes that mirror
    the tags we are looking for, namely they mirror them softly. What I mean
    by this is that if a tag has all the attributes and more of the mirror node
    then it is the same, but if it does not have all of the attributes (as well
    as name) of the mirror node it is different.

    You initialize one of these extractors with an extractors dictionary composed
    of these representative nodes as keys and functions, defined within the object
    which take only a tag as extractors. The extractors then perform some kind
    of action which will add some part of the tag to our structured document. Then
    they each return the next sibling (to be considred). Then the next sibling
    is used until we run out of siblings and the whole document has been parsed.
    But all you need to input is the directory to save the file to, the soup
    you want to parse, and then you must initialize the extractor. Then call Extract
    and you have your document!
    """

    def __init__(self, directory):
        self.directory = directory
        self.ENCODING = 'utf-8'
        self.extractors = {}
        self.initializeState() # useful for store and retrieving state data in extractors
        # these are key value pairs, where the key
        # is a node and the value is a function
        # that handles extraction of a node that compares.
        # to that tag

    def initializeState(self):
        self.state = None

    def AddSoup(self, soup):
        # this allows us to initialize and then reuse this object
        self.soup = soup
        # we also have to start a new document
        self.document = StructuredDocument(self.directory)

    def AddExtractor(self, node, extractor, *args):
        # this allows us to tell our HTML extractor what to do with a tag that
        # soft compares to node
        value = [extractor]
        value.extend(args)
        self.extractors[node] = value

    def ExtractHTML(self):
        # here all we do is start with the top element and roll our way
        # through each sibling element note that to get to the children
        # we will need to define an extractor that causes us to get the
        # children note we start with the HTML and don't concern ourselves
        # with the metadata, this can be changed
        self.extractChildren(self.soup.html)

    def extract(self, tag):
        extractor_set = self.getExtractor(tag)
        extractor = extractor_set[0]
        if len(extractor_set) > 1:
            args = extractor_set[1:]
            return extractor(tag, *args)
        else:
            return extractor(tag)

    def titleExtractor(self, tag):
        # this extracts content into a title tag
        self.document.CreateNode('title')
        self.document.AddContent(tag.get_text())
        self.document.FinishNode()
        return tag.next_sibling

    def extractChildren(self, tag):
        # here we just roll through each of the children and extract if an
        # extractor exists. We ignore the tag itself
        try:
            next_sibling = next(tag.children)
        except:
            next_sibling = None
        while next_sibling:
            next_sibling = self.extract(next_sibling)
        return tag.next_sibling

    def plainTextExtractor(self, tag):
        # for paragraphs and lists we just want to extract the text and then place
        # it in a text element which should be a child if it can be.
        if self.document.current_parent:
            self.document.CreateChild('text')
            self.document.AddContent(tag.get_text())
            self.document.FinishNode()
        else:
            self.document.CreateNode('text')
            self.document.AddContent(tag.get_text())
            self.document.FinishNode()
        return tag.next_sibling

    def rollingExtractor(self, start_tag, child_nodes, end_nodes, name=None):
        # the idea behind this form of extraction is that I start
        # by creating a node for the start_tag with the name of the
        # node being the tag's content. Then we begin to move through
        # the following siblings for that tag and for each check to see
        # if it is in child_tags. If it is not we don't do anything. If
        # it is we extract the data and add it as a child. (note adding)
        # as a child is set as default within the extractor for that tag
        # it is not handled herein (we just set our first tag as a parent)
        # here. Then once we reach one of the end tags we will finish parent
        # and end our extraction.
        # Note this can be nested and that we call default extraction on
        # the child elements here.
        # start_tag should be bs tag and child_tags and end_tags should be
        # document nodes with attributes and a name
        tag_name = start_tag.get_text()
        # note we need to default to making a child in order to nest this
        # function
        if self.document.current_parent:
            self.document.CreateChild(tag_name)
        else:
            self.document.CreateNode(tag_name)
        # now we finish it and set it as the current parent
        self.document.FinishNode(True)

        # next we are going to go through the siblings until we find a stopping
        # tag
        try:
            next_sibling = start_tag.next_sibling
        except:
            next_sibling = None
        while next_sibling:
            is_stopper = False
            for end_node in end_nodes:
                if self.softCompare(next_sibling, end_node):
                    is_stopper = True
                    break
            if is_stopper:
                break
            next_sibling = self.extract(next_sibling)
        # now that we have ended we simply finish of the children
        self.document.FinishChildren()
        return next_sibling

    def softCompare(self, tag, node):
        # 2. I realized that this used in getExtractor will just give the first
        # soft match and not the best, so I am going to allow this to be a bit
        # more explicit about how good the match is. Essentially I am going to
        # return False if there is a mismatch, and then True if there isn't
        # and I will also return the length of the node_attributes being compared
        # to. That way I can choose the one with the greatest number of matches.
        # 1. here we are only comparing tag to what exists in node, they don't have
        # be exactly equal

        # first I am going to make sure that this tag is not a string
        if isinstance(tag, str):
            return (False, 0)

        # now we can treat it as a tag
        if not tag.name == node.name:
            return (False, 0)
        tag_attributes = {}
        for key in tag.attrs:
            tag_attributes[key.encode(self.ENCODING)] = writeValue(tag.attrs[key]).encode(self.ENCODING)
        node_attributes = {}
        for key in node.attributes:
            node_attributes[key.encode(self.ENCODING)] = writeValue(node.attributes[key]).encode(self.ENCODING)

        for key in node_attributes:
            if key in tag_attributes:
                if not tag_attributes[key] == node_attributes[key]:
                    return (False, 0)
            else:
                return (False, 0)

        return (True, len(node_attributes))

    def getExtractor(self, tag):
        # 2. updating for more explicit softCompare
        # 1. this will retrieve the extractor for the tag we have
        extractor = [self.noAction]
        current_match_number = -1   # some nodes won't have attributes
        for node in self.extractors:
            compare = self.softCompare(tag, node)
            if compare[0] == True and compare[1] > current_match_number:
                extractor = self.extractors[node]
                current_match_number = compare[1]
        return extractor

    def noAction(self, tag):
        return tag.next_sibling
