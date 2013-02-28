#!/usr/bin/python
'''
Created on Oct 3, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from parts import PrivateData, ReferencePath
import networkx as nx
import extras.reader as reader

search_paths = nx.all_shortest_paths

def __build_reference_paths(G, paths, offset=None, data=None):
	rps = list()
	for p in paths:
		rp = ReferencePath(p[0])
		for i in xrange(len(p) - 1):
			rp.add_edge(p[i], p[i + 1], label=G[p[i]][p[i + 1]]['label'])
		if offset != None and data != None:
			rp.add_edge(p[-1], data, label=offset)
		rps.append(rp)
	return rps


def by_string(memory_dump, ascii):
	G = memory_dump.memory_graph

	rps = list()
	for n in G.nodes():
		# Avoid Private Data
# 		if isinstance(n, PrivateData):
# 			continue
		for o in n.string_offset(ascii):
			shortest_paths = list()
			for m in md.modules:
				try:
					shortest_paths.extend(search_paths(G, m, n))
				except nx.NetworkXNoPath:
					continue
			rps.extend(__build_reference_paths(G, shortest_paths, o, ascii))
	return rps


def by_address(memory_dump, address):
	# Check if address corresponds to a module
	ds = next((m for m in memory_dump.modules if m.address == address), None)
	# if not, check if it corresponds to a data structure
	if ds == None:
		ds = md.data_structures.get(address)
	# if neither, return empty list
	if ds == None:
		return []

	shortest_paths = list()
	G = memory_dump.memory_graph
	for m in memory_dump.modules:
		try:
			shortest_paths.extend(search_paths(G, m, ds))
		except nx.NetworkXNoPath:
			pass

	return __build_reference_paths(G, shortest_paths)


if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description='List the possible reference \
		paths to the specified data structure in a memory dump. The data structure \
		may be specified by its value or by its address. \
		By default it search for shortest reference paths.')
	parser.add_argument(dest='dump', metavar='dump', help='memory dump file.')
	parser.add_argument('-a', dest='address' , metavar='address', help='address of the data structure.')
	parser.add_argument('-s', dest='ascii', metavar='ascii', help='ASCII ascii value to search for.')
	parser.add_argument('-u', dest='unicode', metavar='unicode', help='Unicode ascii value to search for.')
	parser.add_argument('--All', dest='all', action='store_true', help='search for all simple paths. It may take a long time.')
	args = parser.parse_args()

	md = reader.read_memory_dump(args.dump)
	md.build_memory_graph()

	if args.all:
		search_paths = nx.all_simple_paths

	# Search by address
	if args.address != None:
		rps = by_address(md, int(args.address, 16))
		print('{} paths to data structure 0x{:x}'.format(len(rps), int(args.address, 16)))
	# Search bye ascii value
	elif args.ascii != None:
		rps = by_string(md, args.ascii)
		print('{} paths to the ASCII string {}'.format(len(rps), args.ascii))
	elif args.unicode != None:
		rps = by_string(md, args.unicode.encode('utf16'))
		print('{} paths to the Unicode string {}'.format(len(rps), args.unicode))

	for i, rp in zip(xrange(len(rps)), sorted(rps, key=lambda rp: str(rp.root))):
		print(i, '-', rp)
		nx.write_dot(rps[i].normalize(), '{}-nrp{}.dot'.format(md.name, i))

