'''
Created on Aug 6, 2012

@author: David I. Urbina
'''
from collections import OrderedDict
import networkx as nx
import re
import services

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
		self.pointers = OrderedDict()
		self.hash = None


	def string_offset(self, string):
		pattern = re.compile(string)
		offsets = list()
		for i in xrange(self.offset, self.offset + self.size - len(string)):
			if pattern.search(self.data[i:i + len(string)]) != None:
				offsets.append(i - self.offset)
		return offsets


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


class PrivateData(Segment):
	'''
	Private Data segment.
	'''
	def __repr__(self):
		address = '{:x}'.format(self.address).zfill(8)
		return '<pd a=' + address + ' s=' + repr(self.size) + ' o=' + repr(self.offset) + '>'


	def __str__(self):
		return 'Private Data 0x{:x}({})'.format(self.address, self.size)


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


class ReferencePath(nx.DiGraph):
	'''
	Represents a reference path in memory.
	'''
	def __init__(self, root):
		self.root = root
		nx.DiGraph.__init__(self)


	def __print_node(self, node):
		string = '{}'.format(node)
		suc = self.successors(node)
		if len(suc) > 0:
			string += '[{}]->'.format(self.get_edge_data(node, suc[0])['label'])
			return string + self.__print_node(suc[0])
		return string


	def __str__(self):
		return self.__print_node(self.root)


	def __repr__(self):
		return self.__str__()


	def normalize(self):
		out_node = self.root
		rp = nx.DiGraph()
		in_node = self.successors(out_node)
		out_name = '{}({})'.format(out_node.name, out_node.size)
		rp.add_node(out_name)
		num_node = 0
		gen = services.get_all_the_letters()
		while len(in_node) > 0:
			if not isinstance(in_node[0], DataStructure):
				break
			offset = self.get_edge_data(out_node, in_node[0])['label']
			if out_node.size == in_node[0].size:  # TODO: add shape analysis
	# 			if out_node.pointers.keys() == in_node[0].pointers.keys():
				rp.add_edge(out_name, out_name, label=offset)
			else:
				num_node += 1
				in_name = '{}({})'.format(next(gen), in_node[0].size)
				rp.add_edge(out_name, in_name, label=offset)
				out_name = in_name
			out_node = in_node[0]
			in_node = self.successors(out_node)
		return rp
