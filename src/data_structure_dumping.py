#!/usr/bin/python
'''
Created on Jan 22, 2013

@author: David I. Urbina
'''
from __future__ import print_function
import argparse
import extras.reader as reader
import extras.writer as writer
import sys

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Extract a data structure from a  memory dump.')
	parser.add_argument(dest='address', metavar='address', help='address of the data structure to extract.')
	parser.add_argument(dest='dump', metavar='dump', help='memory dump to extract from.')
	args = parser.parse_args()

	md = reader.read_memory_dump(args.dump)
	md.build_memory_graph()

	for m in md.modules:
		if m.address == int(args.address, 16):
			writer.write_memory_dump_data(args.dump + '-' + args.address + '.core', m.data[m.offset: m.offset + m.size])
			print('Core dump for data structure', args.address , 'written.')
			sys.exit()

	try:
		b = md.data_structures[int(args.address, 16)]
		writer.write_memory_dump_data(args.dump + '-' + args.address + '.core', b.data[b.offset: b.offset + b.size])
		print('Core dump for data structure', args.address , 'written.')
	except KeyError:
		print('Error:', args.address, 'not present in memory dump', args.dump)





