'''
Created on Oct 3, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from parts import ReferecePath, PrivateData
import networkx as nx
import reader

search_paths = nx.all_shortest_paths

def __build_reference_paths(graph, paths, offset=None):
	rps = list()
	for p in paths:
		rp = ReferecePath(str(p[-1]), offset=offset)
		for i in xrange(len(p) - 1, 0, -1):
			rp = ReferecePath(str(p[i - 1]), offset=graph[p[i - 1]][p[i]]['label'], rpath=rp)
		rps.append(rp)
	return rps


def by_string(memory_dump, string):
	G = memory_dump.memory_graph

	rps = list()
	for n in G.nodes():
		# Avoid Private Data
		if isinstance(n, PrivateData):
			continue
		for o in n.string_offset(string):
			shortest_paths = list()
			for m in md.modules:
				try:
					shortest_paths.extend(search_paths(G, m, n))
				except nx.NetworkXNoPath:
					continue
			rps.extend(__build_reference_paths(G, shortest_paths, o))
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
	parser = argparse.ArgumentParser(description='List the possible reference paths to the specified data structure in a memory dump. The data structure may be specified by its value or by its address. By default it search for shortest reference paths.')
	parser.add_argument(dest='dump', metavar='dump', help='memory dump file.')
	parser.add_argument('-a', dest='address' , metavar='address', help='address of the data structure.')
	parser.add_argument('-s', dest='string', metavar='string', help='string value to search for.')
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
	# Search bye string value
	elif args.string != None:
		rps = by_string(md.memory_graph, args.string)
		print('{} paths to string {}'.format(len(rps), args.string))

	for p in sorted(rps, cmp=lambda x, y: cmp(x.name, y.name)):
		print(p)
