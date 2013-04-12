'''
Created on Aug 6, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from memory_graph_generation.memorydump import MemoryDump, CacheDecorator
from parts import Segment, Module, PrivateData
import services

class SegmentType:
    Segment = 1
    Heap = 2
    Module = 3
    Pdata = 4


def read_memory_dump(filename):
    md = MemoryDump(filename)
    md.data = __read_memory_dump_data(filename + '.core')
    md.size = len(md.data)
    md.segments = __read_segments(SegmentType.Segment, filename + '.segments', md.data)
    __calculate_segments_offsets(md, md.segments)
    md.modules = __read_segments(SegmentType.Module, filename + '.modules', md.data)
    __calculate_segments_offsets(md, md.modules)
    md.heaps = __read_segments(SegmentType.Heap, filename + '.heaps', md.data)
    __calculate_segments_offsets(md, md.heaps)
    md.pdata = __read_segments(SegmentType.Pdata, filename + '.pdata', md.data)
    __calculate_segments_offsets(md, md.pdata)
    return CacheDecorator(md)


def __calculate_segments_offsets(memory_dump, segments):
    '''
    Converts list of ranges of virtual addresses to a list of ranges of offset.
    '''
    for s in segments:
        s.offset = services.offset_from_address(memory_dump, s.address)


def __read_memory_dump_data(filename):
    with open(filename, 'rb') as f:
        return f.read()


def __read_segments(stype, filename, data):
    '''
    Read segments of the specified type from file "filename".
    '''
    with open(filename, 'r') as f:
        segments = list()
        for line in f:
            if stype == SegmentType.Module:
                segments.append(Module(int(line.split(':')[0], 16), int(line.split(':')[1], 16), line.split(':')[2].rstrip(), data=data))
            elif stype == SegmentType.Heap:
                segments.append(Segment(int(line.split()[0], 16), int(line.split()[5].replace(',', '')) * 1024, data=data))
            elif stype == SegmentType.Pdata:
# TODO: add Private Data
#                 segments.append(PrivateData(int(line.split()[0], 16), int(line.split()[4].replace(',', '')) * 1024, data=data))
                pass
            else:
                segments.append(Segment(int(line.split(':')[0], 16), int(line.split(':')[1], 16), data=data))
    return segments

