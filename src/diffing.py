'''
Created on Nov 29, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from keyedset import KeyedSet
import reader
import services
import argparse
import math
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np


def __draw_graph_diffing(memory_dump1, memory_dump2, differences):
	plt.subplot(121)
	pos = nx.pygraphviz_layout(memory_dump1.memory_graph, prog='dot')
	nx.draw_networkx_nodes(memory_dump1.memory_graph, pos, memory_dump1.memory_graph.nodes(), node_color='b', node_size=200)
	nx.draw_networkx_nodes(memory_dump1.memory_graph, pos, differences[0], node_color='r', node_size=600)
	nx.draw_networkx_nodes(memory_dump1.memory_graph, pos, differences[2], node_color='y', node_size=600)
	nx.draw_networkx_edges(memory_dump1.memory_graph, pos, memory_dump1.memory_graph.edges())
	nx.draw_networkx_labels(memory_dump1.memory_graph, pos, font_size=8)
	plt.title(memory_dump1.name)
	plt.axis('off')
	plt.subplot(122)
	pos = nx.pygraphviz_layout(memory_dump2.memory_graph, prog='dot')
	nx.draw_networkx_nodes(memory_dump2.memory_graph, pos, memory_dump2.memory_graph.nodes(), node_color='b', node_size=200)
	nx.draw_networkx_nodes(memory_dump2.memory_graph, pos, differences[1], node_color='r', node_size=600)
	nx.draw_networkx_nodes(memory_dump2.memory_graph, pos, differences[3], node_color='g', node_size=600)
	nx.draw_networkx_edges(memory_dump2.memory_graph, pos, memory_dump2.memory_graph.edges())
	nx.draw_networkx_labels(memory_dump2.memory_graph, pos, font_size=8)
	plt.title(memory_dump2.name)
	plt.axis('off')
	lr = plt.Circle((0, 0), 5, fc='r')
	lb = plt.Circle((0, 0), 5, fc='b')
	lg = plt.Circle((0, 0), 5, fc='g')
	ly = plt.Circle((0, 0), 5, fc='y')
	plt.legend([lb, lr, lg, ly], ['No changed', 'Changed', 'Added', 'Removed'], loc=4)
# 	plt.savefig(memory_dump1.name + '-' + memory_dump2.name + '.png')
	plt.show()


def draw_memory_graph_intersection(memory_dumps, nodes):
	pos = nx.pygraphviz_layout(memory_dumps[-1].memory_graph, prog='dot')
	nx.draw_networkx_nodes(memory_dumps[-1].memory_graph, pos, memory_dumps[-1].memory_graph.nodes(), node_color='b', node_size=200)
	nx.draw_networkx_nodes(memory_dumps[-1].memory_graph, pos, nodes, node_color='r', node_size=600)
	nx.draw_networkx_edges(memory_dumps[-1].memory_graph, pos, memory_dumps[-1].memory_graph.edges())
	nx.draw_networkx_labels(memory_dumps[-1].memory_graph, pos, font_size=8)
	plt.title('-'.join((n.name for n in memory_dumps)))
	plt.axis('off')

	lr = plt.Circle((0, 0), 5, fc='r')
	lb = plt.Circle((0, 0), 5, fc='b')
	plt.legend([lb, lr], ['No change', 'Change'], loc=4)
	plt.axis('off')
	plt.show()


def diff_pair_memory_graphs(memory_dump1, memory_dump2):
	diff_globals1 = set(memory_dump1.modules) - set(memory_dump2.modules)
	diff_globals1 = KeyedSet(diff_globals1, key=lambda seg: seg.address)
	diff_globals2 = set(memory_dump2.modules) - set(memory_dump1.modules)
	diff_globals2 = KeyedSet(diff_globals2, key=lambda seg: seg.address)
	changed_globals2 = diff_globals1 & diff_globals2
	changed_globals1 = diff_globals2 & diff_globals1
	removed_globals = diff_globals1 - changed_globals1
	added_globals = diff_globals2 - changed_globals2

	diff_ds1 = set(memory_dump1.data_structures.values()) - set(memory_dump2.data_structures.values())
	diff_ds1 = KeyedSet(diff_ds1, key=lambda seg: seg.address)
	diff_ds2 = set(memory_dump2.data_structures.values()) - set(memory_dump1.data_structures.values())
	diff_ds2 = KeyedSet(diff_ds2, key=lambda seg: seg.address)
	changed_ds2 = diff_ds1 & diff_ds2
	changed_ds1 = diff_ds2 & diff_ds1
	removed_ds = diff_ds1 - changed_ds1
	added_ds = diff_ds2 - changed_ds2

	return (changed_globals1 | changed_ds1, changed_globals2 | changed_ds2, removed_globals | removed_ds, added_globals | added_ds)


def diff_memory_graphs(memory_dumps):
	differences = list()
	for i in xrange(len(memory_dumps) - 1):
		differences.append(diff_pair_memory_graphs(memory_dumps[i], memory_dumps[i + 1]))

	if len(differences) == 1:
		# __draw_graph_diffing(memory_dumps[0], memory_dumps[1], differences[0])
		return (differences[0][1], differences[0][2], differences[0][3])
	else:
		keyedsets1 = list()
		keyedsets2 = list()
		keyedsets3 = list()
		for diff in differences:
			keyedsets1.append(KeyedSet(diff[1], key=lambda seg: seg.address))
			keyedsets2.append(KeyedSet(diff[2], key=lambda seg: seg.address))
			keyedsets3.append(KeyedSet(diff[3], key=lambda seg: seg.address))

		changed = keyedsets1[0]
		for ks in keyedsets1:
			changed = changed & ks

		removed = keyedsets2[0]
		for ks in keyedsets2:
			removed = removed | ks

		added = keyedsets3[0]
		for ks in keyedsets3:
			added = added | ks

		added = added - removed
		last_md = set(memory_dumps[-1].modules) | set(memory_dumps[-1].data_structures.values())
		added = added & KeyedSet(last_md, key=lambda seg: seg.address)

	return (changed, removed, added)


def export_memory_graph_intersection(memory_dumps, intersection):
	graph = memory_dumps[-1].memory_graph.copy()

	nodes = set()
	for m in memory_dumps[-1].modules:
		for i in intersection[0] | intersection[2]:
			try:
				nodes.update(nx.shortest_path(graph, m, i))
			except:
				pass

	for n in graph.nodes()[:]:
		if n not in nodes:
			graph.remove_node(n)

	# for n in graph.nodes()[:]:
		# for i in intersection[0] | intersection[2]:
			# if nx.has_path(graph, n, i):
				# break
		# else:
			# graph.remove_node(n)

	for n in graph.nodes():
		graph.node[n]['color'] = 'turquoise'
	for n in intersection[0]:
		graph.node[n]['color'] = 'red'
		if n in memory_dumps[-1].pdata:
			graph.node[n]['color'] = 'deeppink'
	for n in intersection[2]:
		graph.node[n]['color'] = 'green'
		if n in memory_dumps[-1].pdata:
			graph.node[n]['color'] = 'greenyellow'
	nx.write_dot(graph, '-'.join((n.name for n in memory_dumps)) + '.dot')


def diff_pair_memory_segments(segment1, segment2):
	offsets = list()
	for i in xrange(min(segment1.size, segment2.size)):
		if segment1.data[segment1.offset + i] != segment2.data[segment2.offset + i]:
			offsets.append(i)
	return offsets


def diff_memory_segments(segments):
	sets = list()
	if len(segments) == 2:
		return set(diff_pair_memory_segments(segments[0], segments[1]))
	for i in xrange(len(segments) - 1):
		sets.append(set(diff_pair_memory_segments(segments[i], segments[i + 1])))
	return set.intersection(*sets)


def diff_memory_segments_by_address(address, memory_dumps):
	dss = list()
	for md in memory_dumps:
		for m in md.modules:
			if m.address == address:
				dss.append(m)
				break

	if len(dss) == 0:
		dss = [md.data_structures[address] for md in memory_dumps]

	return diff_memory_segments(dss)


def draw_segments_diffing(segments, offsets):

	size = min([s.size for s in segments])
# 	length = math.ceil(math.sqrt(math.ceil(size / 4)))
	length = math.ceil(math.sqrt(size))
	data = np.zeros((length, length))

	for o in offsets:
# 		j = math.floor((o / 4) / length)
# 		h = (o / 4) % length
		j = math.floor(o / length)
		h = o % length
		data[j][h] = 1

	plt.imshow(data, interpolation="nearest")
	plt.show()


def substract_intersections(memory_dumps, dump, intersec1, intersec2):
	changed1 = KeyedSet(intersec1[0], key=lambda seg: seg.address)
	changed2 = KeyedSet(intersec2[0], key=lambda seg: seg.address)

	inter = changed2 & changed1
	changed = changed1 - inter

	for seg in inter:
		offsets1 = diff_memory_segments_by_address(seg.address, memory_dumps)
		offsets2 = diff_memory_segments_by_address(seg.address, [memory_dumps[-1], dump])
		offsets = offsets1 - offsets2
		if len(offsets) > 0:
			changed.add(seg)

	removed1 = KeyedSet(intersec1[1], key=lambda seg: seg.address)
	removed2 = KeyedSet(intersec2[1], key=lambda seg: seg.address)
	added1 = KeyedSet(intersec1[2], key=lambda seg: seg.address)
	added2 = KeyedSet(intersec2[2], key=lambda seg: seg.address)
	return (changed, removed1 - removed2, added1 - added2)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Diff memory dumps by memory graph.')
	parser.add_argument('-d', required=True, dest='dumps', nargs='+', metavar='memorydump', help='memory dumps to diff.')
	parser.add_argument('-r', dest='substract', metavar='memorydump', help='memory dump to substract.')
	args = parser.parse_args()

	memory_dumps = [reader.read_memory_dump(f) for f in args.dumps]

	for md in memory_dumps:
		md.build_memory_graph()

	intersec1 = diff_memory_graphs(memory_dumps)

	if args.substract != None:
		dump = reader.read_memory_dump(args.substract)
		dump.build_memory_graph()
		intersec2 = diff_memory_graphs([memory_dumps[-1], dump])
		intersec1 = substract_intersections(memory_dumps, dump, intersec1, intersec2)

	export_memory_graph_intersection(memory_dumps, intersec1)

	print('Changed:', len(intersec1[0]))
	services.print_collection(intersec1[0])
	print('Removed:', len(intersec1[1]))
	services.print_collection(intersec1[1])
	print('Added:', len(intersec1[2]))
	services.print_collection(intersec1[2])
