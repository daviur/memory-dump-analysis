'''
Created on Aug 6, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from MemoryDumpParts import DataStructure, Pointer
import MemoryDumpServices
import math
import networkx as nx
import numpy as np
import struct
from collections import OrderedDict
import cPickle

# Renaming function
afo = MemoryDumpServices.address_from_offset
ofa = MemoryDumpServices.offset_from_address

# Global constants
_ALLOC_UNIT_SZ_ = 8
_WORD_SZ_ = 4
_HEAP_SEG_ = 64

class HeapEntryFlags:
    END = 0x10


class CacheDecorator:
    '''
    A cache decorator for MemoryDump class.
    '''
    def __init__(self, decorated):
        '''
        Constructor
        '''
        self.decorated = decorated
        self.segments = self.decorated.segments
        self.offset = self.decorated.offset
        self.size = self.decorated.size
        self.name = self.decorated.name
        self.data = self.decorated.data
        self.modules = self.decorated.modules
        self.g_pointers = decorated.g_pointers
        self.data_structures = decorated.data_structures
        self.memory_graph = self.decorated.memory_graph
        self.calculate_frequencies = self.decorated.calculate_frequencies


    def build_memory_graph(self):
        try:
            with open(self.name + '.cache', 'rb') as f:
                md = cPickle.load(f)
                self.g_pointers = self.decorated.g_pointers = md.g_pointers
                self.data_structures = self.decorated.data_structures = md.data_structures
                self.memory_graph = self.decorated.memory_graph = md.memory_graph
        except:
            self.memory_graph = self.decorated.build_memory_graph()
            self.g_pointers = self.decorated.g_pointers
            self.data_structures = self.decorated.data_structures
            with open(self.name + '.cache', 'wr') as f:
                cPickle.dump(self.decorated, f)
        return self.memory_graph


class MemoryDump:
    '''
    MemoryDump class.
    '''
    def __init__(self, filename):
        '''
        Constructor.
        '''
        self.offset = 0
        self.memory_graph = nx.DiGraph()
        self.data_structures = OrderedDict()
        self.g_pointers = list()
        self.name = filename


    def __parse_heap_entries(self, entry_offset):
        '''
        Parse all the HEAP_ENTRY's starting at the given offset 
        and appends a new data structure per HEAP_ENTRY.
        '''
        last = False
        while not last:
            csize = struct.unpack('<H', self.data[entry_offset:entry_offset + 2])[0]  # current size
#            psize = struct.unpack('<H', self.data[entry_offset + 2:entry_offset + 4])[0] # previous size
            flags = struct.unpack('<B', self.data[entry_offset + 5:entry_offset + 6])[0]  # flags
            ubytes = struct.unpack('<B', self.data[entry_offset + 6:entry_offset + 7])[0]  # unused bytes
            offset = entry_offset + _ALLOC_UNIT_SZ_
            address = afo(self, offset)
            size = (csize * _ALLOC_UNIT_SZ_) - ubytes
            dss = DataStructure(address, offset, size, self.data)
            self.data_structures[dss.address] = dss
            entry_offset += csize * _ALLOC_UNIT_SZ_
            last = flags & HeapEntryFlags.END
        self.memory_graph.add_nodes_from(self.data_structures.values(), color='red', style='filled')


    def __parse_heap_data_structures(self):
#        for (h, d) in zip(self.heaps, self.heaps):
        for h in self.heaps:
#            print('Heap 0x{:x}'.format(d[0]))
            for i in xrange(h.offset + 0x58, h.offset + 0x58 + (_HEAP_SEG_ * _WORD_SZ_), _WORD_SZ_):
                seg_addr = struct.unpack('<I', self.data[i:i + _WORD_SZ_])[0]
                if seg_addr != 0:
#                    print('Segment 0x{:x}'.format(seg_addr))
                    seg_offset = ofa(self, seg_addr)
                    fea = struct.unpack('<I', self.data[seg_offset + 0x20: seg_offset + 0x20 + 4])[0]
                    feo = ofa(self, fea)
#                    print('Entry 0x{:x}'.format(fe))
                    self.__parse_heap_entries(feo)


    def __is_in_heaps(self, word):
        '''
        Determines if a word is pointing to a heap.
        '''
        for h in self.heaps:
            if h.address <= word < h.address + h.size:
                return True
        return False


    def __is_in_heaps_offset(self, offset):
        '''
        Determines if a offset falls inside the pointer destination ranges.
        '''
        for h in self.heaps:
            if h.offset <= offset < h.offset + h.size:
                return True
        return False


    def __is_candidate_pointers(self, addr):
        '''
        verifies if "addr" can be a valid pointer to data structure.
        '''
        return addr % _WORD_SZ_ == 0 and self.__is_in_heaps(addr)


    def __find_global_pointers(self):
        '''
        Finds the list of global pointers making use of the global ranges.
        '''
        self.g_pointers = list()
        for m in self.modules:
            self.memory_graph.add_node(m, color='turquoise', style='filled')
            for o in xrange(m.offset, m.offset + m.size, _WORD_SZ_):
                addr = struct.unpack('<I', self.data[o:o + _WORD_SZ_])[0]
                if self.__is_candidate_pointers(addr):
                    p = Pointer(afo(self, o), o, addr, ofa(self, addr), m)
                    dss = self.data_structures.get(p.d_address)
                    if dss != None:
                        m.pointers.append(p)
                        self.memory_graph.add_edge(m, dss, label=p.offset - m.offset)
#                        self.memory_graph.add_node(p, color='blue', style='filled')
#                        self.memory_graph.add_edge(p, dss, label=0)
            self.g_pointers.extend(m.pointers)


    def __find_data_structure_pointers(self):
        '''
        Finds the pointers in all the data structures in the memory dump.
        '''
        for dss in self.data_structures.values():
            for o in xrange(dss.offset, dss.offset + dss.size, _WORD_SZ_):
                addr = struct.unpack('<I', self.data[o:o + _WORD_SZ_])[0]
                if self.__is_candidate_pointers(addr):
                    p = Pointer(afo(self, o), o, addr, ofa(self, addr), dss)
                    ds2 = self.data_structures.get(p.d_address)
                    if ds2 != None:
                        dss.pointers.append(p)
                        self.memory_graph.add_edge(dss, ds2, label=p.offset - dss.offset)


    def __remove_unreachable(self):
        '''
        Remove all data structures that are not reachable from globals.
        '''
        for dss in self.data_structures.copy().values():
            for m in self.modules:
#            for m in self.g_pointers:
                if nx.has_path(self.memory_graph, m, dss):
                    break
            else:
                self.memory_graph.remove_node(dss)
                del self.data_structures[dss.address]


    def build_memory_graph(self):
        '''
        Builds the memory graph associated with this memory dump.
        '''
        self.__parse_heap_data_structures()
        print('Candidate data structures:', len(self.data_structures))
        self.__find_global_pointers()
        print('Candidate global pointers:', len(self.g_pointers))
        self.__find_data_structure_pointers()
        print("Data structures's pointers found")
        self.__remove_unreachable()
        print('Reachabel data structures:', len(self.data_structures))
        return self.memory_graph


    def calculate_frequencies(self):
        '''
        Calculate the frequencies of each word value in the memory dump.
        '''
        freq = OrderedDict()
        # Count the times a value appears in the memory dump
        for i in xrange(0, self.size, _WORD_SZ_):
            key = struct.unpack('<I', self.data[i:i + _WORD_SZ_])[0]
            v = freq.get(key, 0)
            v += 1
            freq[key] = v

        # Calculates the frequency a value appears.
        for (k, v) in freq.items():
            freq[k] = v * 100 / (self.size / _WORD_SZ_)

        # Calculate the length of the side of the resulting square.
        length = math.ceil(math.sqrt(math.ceil(self.size / _WORD_SZ_)))
        data = np.zeros((length, length))

        # Add the frequencies to the 2d array
        for i in xrange(0, self.size, _WORD_SZ_):
            key = struct.unpack('<I', self.data[i:i + _WORD_SZ_])[0]
            j = math.floor((i / _WORD_SZ_) / length)
            h = (i / _WORD_SZ_) % length
            data[j][h] = freq[key]
#            data[j][h] = k
        return data


if __name__ == '__main__':
    import MemoryDumpReader
    import sys

    filename = sys.argv[1]
    print('Loading memory dump', filename)

    memory_dump = MemoryDumpReader.read_memory_dump(filename)
    memory_dump.build_memory_graph()
    MemoryDumpServices.export_memory_graph(memory_dump)
    MemoryDumpServices.draw_memory_graph(memory_dump)


