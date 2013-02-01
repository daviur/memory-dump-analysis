'''
Created on Aug 6, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from parts import DataStructure, Pointer
import services
import math
import networkx as nx
import numpy as np
import struct
from collections import OrderedDict
import pickle

# Renaming function
afo = services.address_from_offset
ofa = services.offset_from_address

# Global constants
_ALLOC_UNIT_SZ_ = 8
_WORD_SZ_       = 4
_HEAP_SEG_      = 64

class HeapEntryFlags:
    END  = 0x10
    FREE = 0x0


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
        self.pdata = self.decorated.pdata
        self.modules = self.decorated.modules
        self.g_pointers = decorated.g_pointers
        self.data_structures = decorated.data_structures
        self.memory_graph = self.decorated.memory_graph
        self.calculate_frequencies = self.decorated.calculate_frequencies
        self.find_pointers_to_address = self.decorated.find_pointers_to_address


    def build_memory_graph(self):
        try:
            with open(self.name + '.cache', 'rb') as f:
                md = pickle.load(f)
                self.g_pointers = self.decorated.g_pointers = md.g_pointers
                self.data_structures = self.decorated.data_structures = md.data_structures
                self.memory_graph = self.decorated.memory_graph = md.memory_graph
        except:
            self.memory_graph = self.decorated.build_memory_graph()
            self.g_pointers = self.decorated.g_pointers
            self.data_structures = self.decorated.data_structures
            with open(self.name + '.cache', 'wr') as f:
                pickle.dump(self.decorated, f)
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
            #psize = struct.unpack('<H', self.data[entry_offset + 2:entry_offset + 4])[0] # previous size
            flags = struct.unpack('<B', self.data[entry_offset + 5:entry_offset + 6])[0]  # flags
            ubytes = struct.unpack('<B', self.data[entry_offset + 6:entry_offset + 7])[0]  # unused bytes
            offset = entry_offset + _ALLOC_UNIT_SZ_
            address = afo(self, offset)                        
            size = (csize * _ALLOC_UNIT_SZ_) - ubytes            
            if flags != HeapEntryFlags.FREE:                
                dss = DataStructure(address, offset, size, self.data)
                self.data_structures[dss.address] = dss
            entry_offset += csize * _ALLOC_UNIT_SZ_
            last = flags & HeapEntryFlags.END
        self.memory_graph.add_nodes_from(self.data_structures.values(), color='red', style='filled')


    def __parse_heap_data_structures(self):
        for h in self.heaps:
            for i in xrange(h.offset + 0x58, h.offset + 0x58 + (_HEAP_SEG_ * _WORD_SZ_), _WORD_SZ_):
                seg_addr = struct.unpack('<I', self.data[i:i + _WORD_SZ_])[0]
                if seg_addr != 0:
                    seg_offset = ofa(self, seg_addr)
                    fea = struct.unpack('<I', self.data[seg_offset + 0x20: seg_offset + 0x20 + 4])[0]
                    feo = ofa(self, fea)
                    self.__parse_heap_entries(feo)


    def __is_in_segment(self, word, segments):
        '''
        Determines if a word is pointing to a segment.
        '''
        for s in segments:
            if s.address <= word < s.address + s.size:
                return True
        return False            


    def __is_in_heaps(self, word):
        '''
        Determines if a word is pointing to a heap.
        '''
        return self.__is_in_segment(word, self.heaps)

    def __is_in_private_data(self, word):
        '''
        Determines if a word is pointing to a private data segment.
        '''
        return self.__is_in_segment(word, self.pdata) 


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
        #return addr % _WORD_SZ_ == 0 and self.__is_in_heaps(addr)
        return addr % _WORD_SZ_ == 0 and (self.__is_in_heaps(addr) or self.__is_in_private_data(addr))


    def __find_global_pointers(self):
        '''
        Finds the list of global pointers making use of the global ranges.
        '''
        count = 0
        self.g_pointers = list()
        for m in self.modules:
            self.memory_graph.add_node(m, color='turquoise', style='filled')
            if m.size >= _WORD_SZ_:                                 #minimun size is the WORD size
                for o in xrange(m.offset, m.offset + m.size, _WORD_SZ_):
                    addr = struct.unpack('<I', self.data[o:o + _WORD_SZ_])[0]
                    if self.__is_candidate_pointers(addr):
                        p = Pointer(afo(self, o), o, addr, ofa(self, addr), m)
                        dss = self.data_structures.get(p.d_address)
                        if dss != None:
                            count += 1
                            m.pointers.append(p)
                            self.memory_graph.add_edge(m, dss, label=p.offset - m.offset)
                self.g_pointers.extend(m.pointers)    
        return count


    def __find_data_structure_pointers(self):
        '''
        Finds the pointers in all the data structures in the memory dump.
        '''
        count = 0
        for dss in self.data_structures.values():
            if dss.size >= _WORD_SZ_:                               #minimun size is the WORD size
                for o in xrange(dss.offset, dss.offset + dss.size, _WORD_SZ_):
                    addr = struct.unpack('<I', self.data[o:o + _WORD_SZ_])[0]
                    if self.__is_candidate_pointers(addr):
                        p = Pointer(afo(self, o), o, addr, ofa(self, addr), dss)
                        ds2 = self.data_structures.get(p.d_address)
                        if ds2 != None:
                            count += 1
                            dss.pointers.append(p)
                            self.memory_graph.add_edge(dss, ds2, label=p.offset - dss.offset)
        return count


    def __remove_unreachable(self):
        '''
        Remove all data structures that are not reachable from globals.
        '''
        for dss in self.data_structures.copy().values():
            for m in self.modules:
                if nx.has_path(self.memory_graph, m, dss):
                    break
            else:
                self.memory_graph.remove_node(dss)
                del self.data_structures[dss.address]


    def __add_private_data(self):
        for p in self.pdata:            
            self.memory_graph.add_node(p, color='orchid', style='filled')
            self.data_structures[p.address] = p


    def build_memory_graph(self):
        '''
        Builds the memory graph associated with this memory dump.
        '''
        self.__parse_heap_data_structures()
        print('Candidate data structures:', len(self.data_structures))
        self.__add_private_data()
        print('Private data added')
        count = self.__find_global_pointers()
        print('Candidate global pointers:', count)
        count = self.__find_data_structure_pointers()
        print("Data structures's pointers:", count)
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


    def find_pointers_to_address(self, address):
        addresses = list()
        for i in xrange(0, self.size, _WORD_SZ_):
            word = struct.unpack('I', self.data[i:i + _WORD_SZ_])[0]
            if address == word:
                addresses.append(afo(self, i))
        return addresses


if __name__ == '__main__':
    import reader
    import argparse
    import services
    
    parser = argparse.ArgumentParser(description='Performs operations over memory dumps.')    
    parser.add_argument(dest='dump', metavar='dump', help='memory dump file.')    
    parser.add_argument('-o', dest='offset1' , metavar='offset', help='offset to convert to virtual address.')
    parser.add_argument('-f', dest='offset2', metavar='offset', help='offset to find pointers.')
    args = parser.parse_args()

    md = reader.read_memory_dump(args.dump)
    md.build_memory_graph()
    services.export_memory_graph(md)
    #services.draw_memory_graph(md)
    
    if args.offset1 != None:
        print("offset {} corresponds to v-address 0x{:x}".format(args.offset1, services.address_from_offset(md, int(args.offset1, 16))))
    
    if args.offset2 != None:
        pointers = md.find_pointers_to_address(services.address_from_offset(md, int(args.offset2, 16)))        
        for a in pointers:
            print('0x{:x}'.format(a))
        