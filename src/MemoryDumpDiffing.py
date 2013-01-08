'''
Created on Nov 29, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from KeyedSet import KeyedSet
import MemoryDumpReader
import MemoryDumpServices
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
#    plt.savefig(memory_dump1.name + '-' + memory_dump2.name + '.png')
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
#    print('Changed globals: ', len(changed_globals1))
#    print('Removed globals: ', len(removed_globals))
#    print('Added globals: ', len(added_globals))

    diff_ds1 = set(memory_dump1.data_structures.values()) - set(memory_dump2.data_structures.values())
    diff_ds1 = KeyedSet(diff_ds1, key=lambda seg: seg.address)
    diff_ds2 = set(memory_dump2.data_structures.values()) - set(memory_dump1.data_structures.values())
    diff_ds2 = KeyedSet(diff_ds2, key=lambda seg: seg.address)
    changed_ds2 = diff_ds1 & diff_ds2
    changed_ds1 = diff_ds2 & diff_ds1
    removed_ds = diff_ds1 - changed_ds1
    added_ds = diff_ds2 - changed_ds2
#    print('Changed ds: ', len(changed_ds1))
#    print('Removed ds: ', len(removed_ds))
#    print('Added ds: ', len(added_ds))

    return (changed_globals1 | changed_ds1, changed_globals2 | changed_ds2, removed_globals | removed_ds, added_globals | added_ds)


def diff_memory_graphs(memory_dumps):
    differences = list()
    for i in xrange(len(memory_dumps) - 1):
        differences.append(diff_pair_memory_graphs(memory_dumps[i], memory_dumps[i + 1]))

    if len(differences) == 1:
        __draw_graph_diffing(memory_dumps[0], memory_dumps[1], differences[0])
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
#
    for n in graph.nodes()[:]:
        for i in intersection[0] | intersection[2]:
            if nx.has_path(graph, n, i):
                break
        else:
            graph.remove_node(n)
#
    for n in graph.nodes():
        graph.node[n]['color'] = 'turquoise'
    for n in intersection[0]:
        graph.node[n]['color'] = 'red'
    for n in intersection[2]:
        graph.node[n]['color'] = 'green'
    nx.write_dot(graph, '-'.join((n.name for n in memory_dumps)) + '.dot')


def diff_pair_memory_segments(segment1, segment2):
    offsets = list()
    for i in xrange(min(segment1.size, segment2.size)):
        if segment1.data[segment1.offset + i] != segment2.data[segment2.offset + i]:
            offsets.append(i)
    return offsets


def diff_memory_segments(segments):
    sets = list()
    for i in xrange(len(segments) - 1):
        sets.append(set(diff_pair_memory_segments(segments[i], segments[i + 1])))
    return set.intersection(*sets)


def draw_segments_diffing(segments, offsets):

    size = min([s.size for s in segments])
#    length = math.ceil(math.sqrt(math.ceil(size / 4)))
    length = math.ceil(math.sqrt(size))
    data = np.zeros((length, length))

    for o in offsets:
#        j = math.floor((o / 4) / length)
#        h = (o / 4) % length
        j = math.floor(o / length)
        h = o % length
        data[j][h] = 1

    plt.imshow(data, interpolation="nearest")
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compares memory dumps, data structure by data structure.')
    parser.add_argument('-g', dest='graph', action='store_true', help='compares the memory graphs.')
    parser.add_argument(dest='filename' , metavar='memorydump', help='the file name of the memory dump.')
    parser.add_argument(dest='filenames' , nargs='+', metavar='other', help='other files.')
    args = parser.parse_args()

    md1 = MemoryDumpReader.read_memory_dump(args.filename)
    memory_dumps = [md1]
    for f in args.filenames:
        md = MemoryDumpReader.read_memory_dump(f)
        memory_dumps.append(md)

    if args.graph:
        for md in memory_dumps:
            md.build_memory_graph()

        intersection = diff_memory_graphs(memory_dumps)
        export_memory_graph_intersection(memory_dumps, intersection)

        print('Changed:', len(intersection[0]))
        MemoryDumpServices.print_collection(intersection[0])
        print('Removed:', len(intersection[1]))
        MemoryDumpServices.print_collection(intersection[1])
        print('Added:', len(intersection[2]))
        MemoryDumpServices.print_collection(intersection[2])
    else:
        offsets = diff_memory_segments(memory_dumps)
        print('Different offsets:', len(offsets))
        draw_segments_diffing(memory_dumps, offsets)
#        MemoryDumpServices.print_collection(offsets)
