# Python File xmlextractor.py
"""
This file contains the class we need for extracting an xml document
into a structured document. (Really this just works for documents
structured with tags).

Now such a document works in the following way: we expect tags of
the following forms:
<name attrs>        start tag
</name>             end tag
<name attrs />      complete tag

Now complete tags are easy, they stand alone and have no chidren. And
start tags would be easy too, if it wasn't for the fact that sometimes
you can find them alone too... This complicates waiting for end tags.

In the normal case (where you don't have standalone) start tags the logic
is as follows. Create a tag when you find a start tag, and give it the right
attributes. Then, grab all of the content that isn't tags before the next
start tag or end tag, this is that tag's content. Then, if the first one you
find is an end tag, go ahead and finish the tag without setting it up as a
parent. Otherwise, set it up as a parent and close the parentage once you hit
its end tag. (That is you keep track of the depth level and the first end tag
at that level is going to be the signal to go up in parentage).

Now, one will note that to handle start tags with no end tag, we have to leave
nodes unfinished before going onto the next node, StructureDocument won't let us
do this (which is exactly what I wanted). So, we will assume we are working with
well formatted xml or html.
"""
from markupcreator import StructuredDocument
import re

class XMLExtractor:

    def __init__(self, directory=''):
        self.document = StructuredDocument(directory)
        self.directory = directory
        self.special = {}
        self.file = None
        self.tag_expression = re.compile('<(\/)?([^ <>\/]*)?( [^<>\/]*)? *(\/)?>')
            # the first group in that will hold the / if it exist at the beginning
            # the second group holds the first thing in our tag besides. If it is
            # a special character we will have a special way of handling it and so
            # can leave the rest be, and then the third group is the rest of the stuff
            # and finally the fourth group is a / if there is one.
        self.attribute_expression = re.compile('([^ =]*)=([^ =]*)')
            # this should be used on group three when our group 2 is not special
            # and group one is empty. This, using findall, will then grab all of
            # the attribute pairs and put the name in group one and the value (with
            # or without parenthesis) into group two
        self.Initiate()

    """
    Now we know that there are more tags than just the ones mentioned above.
    For example xml starts with <?xml version... ?>. Therefore we are going
    to want to watch for special characters and strings at the beginnings of tags.
    Thus I have put the special dictionary above. The dictionary's keys are the
    special strings and the second is a function defined herein that plays with
    the structured document. Therefore this is quite like the htmlextractor.
    Except I am going to add Initiate here instead of in a class taking advantage
    of it.

    Note that extractors are not defined for normal XML tags. Reason is there
    SHOULD NOT be special attention paid to these, all should be treated the same
    we aren't doing anything fancy here.
    """

    def Initiate(self):
        # this is where you set the extractors in self.special this will be
        # called on initiation
        # the extractor should take the match object from the regular expression
        # as its argument (additional ones can be supplied as in our other code)
        self.special['!--'] = [self.doNothing]
        """
        NOTE COMMENTS CANNOT HAVE TAGS INSIDE OF THEM! YOU HAVE TO STRIP SUCH
        TAGS FIRST!!!!
        """
        self.special['?xml'] = [self.doNothing]


    def doNothing(self, tag):
        pass

    """
    The following method works in the following way:
    First it checks to make sure we have a file ready to be opened.
    Then it grabs the contents of that file.
    Then it applies finditer on the file using the tag expression.
    Then, it finds the first expression. If it is special it runs the
    special extractor using the dictionary attached to self.
    If it is not special it checks to see what the first group is like

    When we hit a node we first check to make sure it is not special, if it
    is we call its extractor and end the day. If not we go through the following

    First we check to make sure it is not a complete tag, because if it is
    the whole process is rather easy.

    If group one is empty, first we check to see if the last tag also had group
    one empty. If so, we finish the last node as a parent. Then we add the name
    of the tag to the end of a name list
    and create the node. Then we pull attributes if there are any and then grab
    the content before the next tag match. This is put into the node.

    If group one is not empty, we first look to check its name is the same
    as the last name in the name list. If it is then we make the next check:
    we check to see if the last tag found also had a non-empty group one. If so
    we finish children and jump up a parent, if not we finish the previous node.

    """
    def InputFile(self, address):
        self.file = open(address, 'rb')

    def CreateDocument(self):
        if not self.file:
            return
        # now we flush the self.document
        self.document = StructuredDocument(self.directory)
        # read the file
        contents = self.file.read()

        # declaration of variables that will be used in the following loop
        content_between_tags = ''
        names = []
        previous_group1_content = True # for correct behavior
        previous_tag_end = 0
        previous_tag_complete = False
        for match in re.finditer(self.tag_expression, contents):
            if match.group(2) in self.special:
                self.extract(match.group(2)) # extract
                continue
            content_between_tags = contents[previous_tag_end: match.start()]
            if not match.group(1):
                if previous_group1_content == False and not previous_tag_complete:
                    # here we need to finish the last node as a parent
                    self.document.AddContent(content_between_tags.decode('utf-8'))
                    self.document.FinishNode(True)
                # now we handle the current node
                name = match.group(2)
                names.append(name)
                if self.document.current_parent:
                    self.document.CreateChild(name)
                else:
                    self.document.CreateNode(name)
                # now we need to get the attributes
                if match.group(3):
                    self.document.AddAttributes(**self.grabAttributes(match.group(3)))
                # the following handles complete tags
                previous_tag_complete = False
                if match.group(4) == '/':
                    previous_tag_complete = True
                    self.document.FinishNode()
                    names = names[:-1] # remove the name we just added as it is finished
                previous_group1_content = False # set for the next round
                previous_tag_end = match.end()
            elif match.group(1) == '/':
                if match.group(2) != names[-1]:
                    # in this case we have a serious problem
                    print('Problem with structured syntax with tag: ' + match.group(0))
                    return
                # now we can just check to see if we are jumping up a parent.
                if previous_group1_content == True or previous_tag_complete:
                    # now we know we are finishing off a parent (which means the
                    # node has been finished but we need to finish children)
                    self.document.FinishChildren()
                elif previous_group1_content == False and not previous_tag_complete:
                    # we first need to add the content before we finish
                    content_between_tags = contents[previous_tag_end: match.start()]
                    self.document.AddContent(content_between_tags.decode('utf-8'))
                    self.document.FinishNode()
                names = names[:-1] # we should remove this name now
                previous_group1_content = True
                previous_tag_end = match.end()
                previous_tag_complete = False



    def grabAttributes(self, attributes_string):
        attributes = {}
        for match in re.finditer(self.attribute_expression, attributes_string):
                attributes[match.group(1)] = match.group(2)
        return attributes

    def extract(self, string):
        if string not in self.special:
            return
        extractor_set = self.special[string]
        extractor = extractor_set[0]
        if len(extractor_set) > 1:
            args = extractor_set[1:]
            return extractor(string, *args)
        else:
            return extractor(string)
