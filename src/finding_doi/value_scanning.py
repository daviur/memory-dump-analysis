#!/usr/bin/python
'''
Created on Nov 30, 2012

@author: David I. Urbina
'''
from __future__ import print_function
import argparse
import diffing
import reader
import services
import struct


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
	parser = argparse.ArgumentParser(description='Search for values in the intersection of memory dumps.')
	parser.add_argument('-d', required=True, dest='dumps' , nargs='+', metavar='memorydumps', help='memory dump files.')
	parser.add_argument('-v', required=True, dest='values', nargs='+', metavar='values', help='value corresponding to each memory dump.')
	args = parser.parse_args()

	memory_dumps = [reader.read_memory_dump(f) for f in args.dumps]

	if len(memory_dumps) == 1:
		offsets = find_value(memory_dumps[0], args.values[0])
		print('Number of candidate offsets:', len(offsets))

		for (o, t) in offsets:
			print('0x{:x}'.format(services.address_from_offset(memory_dumps[0], o)), t)
	else:
		intersection = diffing.diff_memory_segments(memory_dumps)

		print('TODO: finish intersection by value')
