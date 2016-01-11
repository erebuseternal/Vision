# Python File functions.py

def chunkGenerator(line, num_pieces=None):
    # this is a generator which each time it is called cuts the next bit
    # of text before the first space (after stripping whitespace off the
    # ends) and then returns that bit. Once it gets called num_pieces
    # times it just returns the rest of the line
    # if num-pieces is not specified, it finds as many chunks as it can
    times_called = 1
    while True:
        line = line.strip()
        if num_pieces and times_called == num_pieces:
            break
        next_space = line.find(' ')
        if next_space == -1:
            break   # we've run out of spaces so stop the iterator
        chunk, line = line[0:next_space], line[next_space:]
        times_called = times_called + 1
        yield chunk
    yield line  # as our final piece we yield the rest of the line

class Issue(Exception):
    def __init__(self, problem):
        self.problem = problem
    def __str__(self):
        return 'ERROR: the problem was: %s' % self.problem

class Verbose:
    v = 4

    def VP(self, string, level=1):
        if self.v >= level:
            print(string)
