#!/usr/bin/python
'''
Created on Nov 30, 2012

@author: David I. Urbina
'''
from __future__ import print_function
import argparse
import extras.reader as reader
import extras.services as services
import finding_doi.memory_diffing as diffing
import struct
from extras.keyedset import KeyedSet


class Encoding:
	def __init__(self, form, size, name):
		self.format = form
		self.size = size
		self.type = name


encodings = [Encoding('<d', 8, 'double'), Encoding('<Q', 8, 'long'), Encoding('<I', 4, 'integer'),
			 Encoding('<f', 4, 'float'), Encoding('<H', 2, 'short'), Encoding('<B', 1, 'char')]


def number_offset(segment, value):
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


def __decode_offset(seg, enc, o):
	return struct.unpack(enc.format, seg.data[seg.offset + o:seg.offset + o + enc.size])[0]


def get_possible_values(segment, offset):
	return [(enc.type, __decode_offset(segment, enc, offset)) for enc in encodings]


def offsets_in_node(n, enc_type, value):
	if enc_type == 'string':
		return n.string_offset(value)
	else:
		return n.number_offset(float(value))


def offsets_in_graph(graph, enc_type, value):
	vob = dict()
	for n in graph.nodes():
		vob[n] = set(offsets_in_node(n, enc_type, value))
	return vob


def offsets_in_diffing(pos_dumps, values, diffing, enc_type):
	obd = dict()  # Offsets by buffer by memory dump
	for b in diffing[0]:
		obd[b] = dict()
		for (d, v) in zip(pos_dumps, values):
			for n in d.memory_graph.nodes():
				if n.address == b.address:
					obd[b][d] = offsets_in_node(n, enc_type, v)

	ob = dict()  # Offsets by buffer
	for b in diffing[0]:
		ob[b] = set(obd[b][pos_dumps[0]])
		for o in obd[b].values():
			ob[b].intersection_update(o)

	for b in diffing[2]:
		for (md, v) in zip(pos_dumps, values):
			if b in KeyedSet(md.memory_graph.nodes(), key=lambda seg: seg.address):
				ob[b] = offsets_in_node(b, enc_type, v)
				break

	return ob


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Search for values in a memory\
		graph or the intersection of memory graphs.')
	parser.add_argument('-d', required=True, dest='dumps' , nargs='+',
					metavar='dumps', help='memory dump files.')
	parser.add_argument('-v', required=True, dest='values', nargs='+',
					metavar='values',
					help='value corresponding to each memory dump.')
	args = parser.parse_args()

	pos_dumps = [reader.read_memory_dump(f) for f in args.dumps]

	if len(pos_dumps) == 1:
		offsets = number_offset(pos_dumps[0], args.values[0])
		print('Number of candidate offsets:', len(offsets))

		for (o, t) in offsets:
			print('0x{:x}'.format(services.address_from_offset(pos_dumps[0], o)), t)
	else:
		intersection = diffing.diff_memory_segments(pos_dumps)

		print('TODO: finish intersection by value')
