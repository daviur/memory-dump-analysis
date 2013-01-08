'''
Created on Nov 30, 2012

@author: David I. Urbina
'''
from __future__ import print_function
import MemoryDumpReader
import struct
import sys
import MemoryDumpServices


class Encoding:
    def __init__(self, form, size, name):
        self.format = form
        self.size = size
        self.type = name


encodings = [Encoding('<d', 8, 'double'), Encoding('<Q', 8, 'long'), Encoding('<I', 4, 'integer'),
             Encoding('<f', 4, 'float'), Encoding('<H', 2, 'short'), Encoding('<B', 1, 'char')]


def find_value(segment, value):
    '''
    Finds the list of offsets of a segment containing a specific value.
    '''
    offsets = list()
    print('Segment size:', segment.size, 'bytes')
    for i in xrange(segment.offset, segment.offset + segment.size):
        for enc in encodings:
            if i + enc.size <= segment.offset + segment.size:
                word = __decode_offset(segment, enc, i)
                if word == int(value):
                    offsets.append((i, enc.type))
                    break
    return offsets


def __decode_offset(seg, enc, os):
    return struct.unpack(enc.format, seg.data[seg.offset + os:seg.offset + os + enc.size])[0]


def get_possible_values(segment, offset):
    return [(enc.type, __decode_offset(segment, enc, offset)) for enc in encodings]


if __name__ == '__main__':
    filename = sys.argv[1]
    value = sys.argv[2]

    md = MemoryDumpReader.read_memory_dump(filename)
    md.build_memory_graph()
#    offsets = find_value(md.data_structures[0x344c68], value)
    offsets = find_value(md, value)
    print('Number of candidate offsets:', len(offsets))

    for (o, t) in offsets:
        print('0x{:x}'.format(MemoryDumpServices.address_from_offset(md, o)), t)
