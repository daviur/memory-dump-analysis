'''
Created on Aug 6, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from memory_graph_generation.memorydump import MemoryDump, CacheDecorator
from parts import Segment, Module, Stack
import services


def read_memory_dump(filename):
    md = MemoryDump(filename)
    md.data = _read_memory_dump_data(filename + '.core')
    md.size = len(md.data)
    md.segments = _read_metadata(SegmentType.Segment,
                                            filename + '.segments', md.data)
    _calculate_segments_offsets(md, md.segments)
    md.modules = _read_metadata(SegmentType.Module,
                                                filename + '.modules', md.data)
    _calculate_segments_offsets(md, md.modules)
    md.heaps = _read_metadata(SegmentType.Heap, filename + '.heap', md.data)
    _calculate_segments_offsets(md, md.heaps)
    md.pdata = _read_metadata(SegmentType.Pdata, filename + '.pdata', md.data)
    _calculate_segments_offsets(md, md.pdata)
    md.stack = _read_metadata(SegmentType.Stack, filename + '.stack', md.data)
    _calculate_segments_offsets(md, md.stack)
    return CacheDecorator(md)


def _calculate_segments_offsets(memory_dump, segments):
    '''
    Converts list of ranges of virtual addresses to a list of ranges of offset.
    '''
    for s in segments:
        s.offset = services.offset_from_address(memory_dump, s.address)


def _read_memory_dump_data(filename):
    with open(filename, 'rb') as f:
        return f.read()


def _read_metadata(mdtype, filename, data):
    '''
    Read segments of the specified type from file "filename".
    '''
    with open(filename, 'r') as f:
        segments = list()
        for line in f:
            if mdtype == SegmentType.Module:
                segments.append(Module(int(line.split(':')[0], 16),
                                    int(line.split(':')[1], 16),
                                    line.split(':')[2].rstrip(), data=data))
            elif mdtype == SegmentType.Heap:
                segments.append(Segment(int(line.split()[0], 16),
                    int(line.split()[5].replace(',', '')) * 1024, data=data))
            elif mdtype == SegmentType.Pdata:
# TODO: add Private Data
#                 segments.append(PrivateData(int(line.split()[0], 16),
#                     int(line.split()[4].replace(',', '')) * 1024, data=data))
                pass
            elif mdtype == SegmentType.Stack:
                segments.append(Stack(int(line.split()[0], 16),
                      int(line.split()[4].replace(',', '')) * 1024, data=data))
            else:
                segments.append(Segment(int(line.split(':')[0], 16),
                                    int(line.split(':')[1], 16), data=data))
    return segments


class SegmentType:
    Segment = 1
    Heap = 2
    Module = 3
    Pdata = 4
    Stack = 5
