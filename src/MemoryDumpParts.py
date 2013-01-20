'''
Created on Aug 6, 2012

@author: David I. Urbina
'''
class Segment:
    '''
    Describes a section of the core dump file.
    '''
    def __init__(self, address, size, offset=None, data=None):
        '''
        Constructor
        '''
        self.address = address
        self.size = size
        self.offset = offset
        self.data = data
        self.pointers = list()
        self.hash = None


    def __repr__(self):
        address = '{:x}'.format(self.address).zfill(8)
        return '<seg a=' + address + ' s=' + repr(self.size) + ' o=' + repr(self.offset) + '>'


    def __str__(self):
        return '0x{:x}({})'.format(self.address, self.size)


    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


    def __hash__(self):
        if self.hash == None:
            self.hash = hash(repr(self.address) + repr(self.size) + repr(self.data[self.offset: self.offset + self.size]))
        return  self.hash


class Module(Segment):
    '''
    Module class.
    '''
    def __init__(self, address, size, name, data=None):
        '''
        Constructor
        '''
        Segment.__init__(self, address, size, data=data)
        self.name = name


    def __repr__(self):
        address = '{:x}'.format(self.address).zfill(8)
        return '<mod a=' + address + ' s=' + repr(self.size) + ' o=' + repr(self.offset) + ' n=' + self.name + '>'


    def __str__(self):
        return '{} 0x{:x}({})'.format(self.name, self.address, self.size)


class DataStructure(Segment):
    '''
    Represents a data structure in the core dump.
    '''
    def __init__(self, address, offset, size, data=None):
        '''
        Constructor
        '''
        Segment.__init__(self, address, size, data=data, offset=offset)


    def __repr__(self):
        return '<ds a=0x{:x} o={} s={} #pointers={}>'.format(self.address, self.offset, self.size, len(self.pointers))


class Pointer(Segment):
    '''
    Describes a Pointer.
    '''
    def __init__(self, address, offset, d_address, d_offset, segment):
        '''
        Constructor
        '''
        Segment.__init__(self, address, 4, offset=offset)
        self.d_address = d_address
        self.d_offset = d_offset
        self.segment = segment


    def __repr__(self):
        return '<p a=0x{:x} o={} da=0x{:x} do={}>'.format(self.address, self.offset, self.d_address, self.d_offset)


    def __str__(self):
        return '{}+0x{:x}'.format(self.segment, self.offset - self.segment.offset)


    def __hash__(self):
        if self.hash == None:
            self.hash = hash(repr(self.address) + repr(self.offset) + repr(self.d_address) + repr(self.d_offset))
        return self.hash

