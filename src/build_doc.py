#!/usr/bin/python3

# do some basic preprocessing:
# * handle #include directives
# * skip outputting certain comments, in the markdown and in included files

import sys

infile = sys.argv[1]
outfile = sys.argv[2]


def readlines(filename):
    with open(filename, 'r') as fp:
        return fp.readlines()


with open(outfile, 'w') as fp:
    for line in readlines(infile):
        tokens = line.split(' ')
        if tokens[0] == '#include':
            filename = tokens[1].split('"')[1]
            for includeline in readlines(filename):
                if not includeline.startswith('##'):
                    fp.write(includeline)
        elif tokens[0] == '%%':
            continue
        else:
            fp.write(line)
