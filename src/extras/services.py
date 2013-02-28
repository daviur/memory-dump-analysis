'''
Created on Dec 3, 2012

@author: David I. Urbina
'''
import matplotlib.pyplot as plt
import networkx as nx


def print_collection(collection):
	for i in collection:
		print(repr(i))


def address_from_offset(memory_dump, offset):
	'''
	Return the virtual address corresponding to an offset in the memory dump.
	'''
	temp_offset = 0
	for s in memory_dump.segments:
		if temp_offset + s.size >= offset:
			return s.address + offset - temp_offset
		else:
			temp_offset += s.size
	return 0


def offset_from_address(memory_dump, address):
	'''
	Return the offset in the memory dump corresponding to a virtual address.
	'''
	temp_offset = 0
	for s in memory_dump.segments:
		if s.address <= address:
			if s.address + s.size >= address:
				return temp_offset + address - s.address
			else:
				temp_offset += s.size
		else:
			return None


def export_memory_graph(memory_dump):
	nx.write_dot(memory_dump.memory_graph, memory_dump.name + '.dot')


def draw_memory_graph(memory_dump):
	plt.title(memory_dump.name)
# 	pos = nx.spring_layout(memory_dump.memory_graph, iterations=10)
	pos = nx.pygraphviz_layout(memory_dump.memory_graph, prog='dot')
	nx.draw_networkx_nodes(memory_dump.memory_graph, pos, memory_dump.data_structures.values(), node_size=200, node_color='r')
	nx.draw_networkx_nodes(memory_dump.memory_graph, pos, memory_dump.modules, node_color='b', node_size=200)
	# nx.draw_networkx_nodes(memory_dump.memory_graph, pos, memory_dump.g_pointers, node_color='b', node_size=200)
	nx.draw_networkx_edges(memory_dump.memory_graph, pos, memory_dump.memory_graph.edges())
	nx.draw_networkx_labels(memory_dump.memory_graph, pos, font_size=8)

	lr = plt.Circle((0, 0), 5, fc='r')
	lb = plt.Circle((0, 0), 5, fc='b')
	plt.legend([lb, lr], ['Global Pointer', 'Data Structure'], loc=4)
	plt.axis('off')
	plt.savefig(memory_dump.name + '_memory_graph.png')
	plt.show()


def get_all_the_letters(begin='A', end='Z'):
	beginNum = ord(begin)
	endNum = ord(end)
	for number in xrange(beginNum, endNum + 1):
		yield chr(number)
