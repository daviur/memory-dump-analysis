#!/usr/bin/env python
'''
Created on Nov 29, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from extras import reader, services
from extras.keyedset import KeyedSet
import argparse
import math
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import sys

search_paths = nx.all_shortest_paths
# search_paths = nx.all_simple_paths


def _draw_graph_diffing(memory_dump1, memory_dump2, differences):
    plt.subplot(121)
    pos = nx.pygraphviz_layout(memory_dump1.memory_graph, prog='dot')
    nx.draw_networkx_nodes(memory_dump1.memory_graph, pos,
           memory_dump1.memory_graph.nodes(), node_color='b', node_size=200)
    nx.draw_networkx_nodes(memory_dump1.memory_graph, pos, differences[0],
                                                node_color='r', node_size=600)
    nx.draw_networkx_nodes(memory_dump1.memory_graph, pos, differences[2],
                                                node_color='y', node_size=600)
    nx.draw_networkx_edges(memory_dump1.memory_graph, pos,
                                            memory_dump1.memory_graph.edges())
    nx.draw_networkx_labels(memory_dump1.memory_graph, pos, font_size=8)
    plt.title(memory_dump1.name)
    plt.axis('off')
    plt.subplot(122)
    pos = nx.pygraphviz_layout(memory_dump2.memory_graph, prog='dot')
    nx.draw_networkx_nodes(memory_dump2.memory_graph, pos,
            memory_dump2.memory_graph.nodes(), node_color='b', node_size=200)
    nx.draw_networkx_nodes(memory_dump2.memory_graph, pos, differences[1],
                                                node_color='r', node_size=600)
    nx.draw_networkx_nodes(memory_dump2.memory_graph, pos, differences[3],
                                                node_color='g', node_size=600)
    nx.draw_networkx_edges(memory_dump2.memory_graph, pos,
                                            memory_dump2.memory_graph.edges())
    nx.draw_networkx_labels(memory_dump2.memory_graph, pos, font_size=8)
    plt.title(memory_dump2.name)
    plt.axis('off')
    lr = plt.Circle((0, 0), 5, fc='r')
    lb = plt.Circle((0, 0), 5, fc='b')
    lg = plt.Circle((0, 0), 5, fc='g')
    ly = plt.Circle((0, 0), 5, fc='y')
    plt.legend([lb, lr, lg, ly], ['No changed', 'Changed', 'Added',
                                                            'Removed'], loc=4)
#     plt.savefig(memory_dump1.name + '-' + memory_dump2.name + '.png')
    plt.show()


def draw_memory_graph_intersection(pos_dumps, nodes):
    pos = nx.pygraphviz_layout(pos_dumps[-1].memory_graph, prog='dot')
    nx.draw_networkx_nodes(pos_dumps[-1].memory_graph, pos,
           pos_dumps[-1].memory_graph.nodes(), node_color='b', node_size=200)
    nx.draw_networkx_nodes(pos_dumps[-1].memory_graph, pos, nodes,
                                                node_color='r', node_size=600)
    nx.draw_networkx_edges(pos_dumps[-1].memory_graph, pos,
                                            pos_dumps[-1].memory_graph.edges())
    nx.draw_networkx_labels(pos_dumps[-1].memory_graph, pos, font_size=8)
    plt.title('-'.join((n.name for n in pos_dumps)))
    plt.axis('off')

    lr = plt.Circle((0, 0), 5, fc='r')
    lb = plt.Circle((0, 0), 5, fc='b')
    plt.legend([lb, lr], ['No change', 'Change'], loc=4)
    plt.axis('off')
    plt.show()


def diff_pair_memory_graphs(memory_dump1, memory_dump2):
    graph1 = memory_dump1.memory_graph
    graph2 = memory_dump2.memory_graph
    diff_nodes1 = set(graph1.nodes()) - set(graph2.nodes())
    diff_nodes2 = set(graph2.nodes()) - set(graph1.nodes())
    diff_nodes1 = KeyedSet(diff_nodes1, key=lambda buf: str(buf))
    diff_nodes2 = KeyedSet(diff_nodes2, key=lambda buf: str(buf))
    changed_nodes2 = diff_nodes1 & diff_nodes2
    changed_nodes1 = diff_nodes2 & diff_nodes1
    removed_nodes = diff_nodes1 - changed_nodes1
    added_nodes = diff_nodes2 - changed_nodes2
    return (changed_nodes1, changed_nodes2, removed_nodes, added_nodes)


def diff_memory_graphs(dumps):
    differences = list()
    for i in xrange(len(dumps) - 1):
        differences.append(diff_pair_memory_graphs(dumps[i], dumps[i + 1]))

    if len(differences) == 1:
        # _draw_graph_diffing(dumps[0], dumps[1], differences[0])
        return (differences[0][1], differences[0][2], differences[0][3])
    else:
        keyedsets1 = list()
        keyedsets2 = list()
        keyedsets3 = list()
        for diff in differences:
            keyedsets1.append(KeyedSet(diff[1], key=lambda seg: str(seg)))
            keyedsets2.append(KeyedSet(diff[2], key=lambda seg: str(seg)))
            keyedsets3.append(KeyedSet(diff[3], key=lambda seg: str(seg)))

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
        last_md = set(dumps[-1].memory_graph.nodes())
        added = added & KeyedSet(last_md, key=lambda seg: str(seg))

    return (changed, removed, added)


def extract_diff_graph(dump, diff):
    diff_graph = dump.memory_graph.copy()
    diff_graph.roots = list()
    nodes = set()
    for m in dump.modules:
        for i in diff[0] | diff[2]:
            if m == i:
                nodes.add(m)
            try:
                nodes.update(*list(search_paths(diff_graph, m, i)))
            except:
                pass
        if m in nodes:
            diff_graph.roots.append(m)

    for s in dump.stack:
        for i in diff[0] | diff[2]:
            if s == i:
                nodes.add(s)
            try:
                nodes.update(*list(search_paths(diff_graph, s, i)))
            except:
                pass
        if s in nodes:
            diff_graph.roots.append(s)
    for n in diff_graph.nodes()[:]:
        if n not in nodes:
            diff_graph.remove_node(n)
    for n in diff_graph.nodes():
        diff_graph.node[n]['color'] = 'turquoise'
    for n in diff[0]:
        diff_graph.node[n]['color'] = 'red'
        if n in dump.pdata:
            diff_graph.node[n]['color'] = 'deeppink'
    for n in diff[2]:
        diff_graph.node[n]['color'] = 'green'
    nx.write_dot(diff_graph, 'diff_graph.dot')
    return diff_graph


def diff_pair_memory_segments(segment1, segment2):
    offsets = list()
    for i in xrange(min(segment1.size, segment2.size)):
        if segment1.data[segment1.offset + i] != segment2.data[
                                                        segment2.offset + i]:
            offsets.append(i)
    return offsets


def diff_memory_segments(segments):
    sets = list()
    if len(segments) == 2:
        return set(diff_pair_memory_segments(segments[0], segments[1]))
    for i in xrange(len(segments) - 1):
        sets.append(set(diff_pair_memory_segments(segments[i],
                                                            segments[i + 1])))
    return set.intersection(*sets)


def diff_memory_segments_by_address(address, dumps):
    dss = list()
    for md in dumps:
        for n in md.memory_graph.nodes():
            if n.address == address:
                dss.append(n)
                break
        else:
            # Dump md does not containt segment at address
            return set()

    return diff_memory_segments(dss)


def draw_segments_diffing(segments, offsets):

    size = min([s.size for s in segments])
#     length = math.ceil(math.sqrt(math.ceil(size / 4)))
    length = math.ceil(math.sqrt(size))
    data = np.zeros((length, length))

    for o in offsets:
#         j = math.floor((o / 4) / length)
#         h = (o / 4) % length
        j = math.floor(o / length)
        h = o % length
        data[j][h] = 1

    plt.imshow(data, interpolation="nearest")
    plt.show()


def substract_intersections(dumps1, dumps2, intersec1, intersec2):
    '''
    Subtracts the intersection of two sets of memorydumps.
    '''
    changed1 = KeyedSet(intersec1[0], key=lambda seg: seg.address)
    changed2 = KeyedSet(intersec2[0], key=lambda seg: seg.address)

    # Intersection of the "changed" buffers of both sets
    inter = changed2 & changed1
    # Subtracting the "changed" buffers
    changed = changed1 - inter

    for seg in inter:
        offsets1 = diff_memory_segments_by_address(seg.address, dumps1)
        offsets2 = diff_memory_segments_by_address(seg.address, dumps2)
        # If more offsets changed in the intersection 1 than in intersection 2
        # for a given buffer, add the buffer to the resulting
        # "changed" set of buffers
        if len(offsets1 - offsets2) > 0:
            changed.add(seg)

    removed1 = KeyedSet(intersec1[1], key=lambda seg: seg.address)
    removed2 = KeyedSet(intersec2[1], key=lambda seg: seg.address)
    added1 = KeyedSet(intersec1[2], key=lambda seg: seg.address)
    added2 = KeyedSet(intersec2[2], key=lambda seg: seg.address)
    return (changed, removed1 - removed2, added1 - added2)


def process_command_line(argv):
    '''
    Return a 2-tuple: (positive dumps, negative dump).
    "argv" is a list of arguments, or "None" for "sys.argv[1:]".
    '''
    if argv is None:
        argv = sys.argv[1:]
    # initializing the parser object
    parser = argparse.ArgumentParser(
                             description='Diff memory dumps by memory graph.')
    # defining command options
#     parser.add_argument('-g', dest='type_diff', help='')
    parser.add_argument('-p', required=True, dest='pos_dumps', nargs='+',
                metavar='dump', help='positive action memory dumps to diff.')
    parser.add_argument('-n', dest='neg_dump', metavar='dump',
                        help='negative action memory dump to substract.')
    # parsing arguments
    args = parser.parse_args()

    return args.pos_dumps, args.neg_dump  # , args.type_diff


# def method to diff whole dump():


def main(argv=None):
    pdumps, ndump = process_command_line(argv)

    dtype = False

    pos_dumps = [reader.read_memory_dump(f) for f in pdumps]
    if not dtype:
        for md in pos_dumps:
            md.build_memory_graph()

        intersec1 = diff_memory_graphs(pos_dumps)

        if ndump is not None:
            neg_dump = reader.read_memory_dump(ndump)
            neg_dump.build_memory_graph()
            intersec2 = diff_memory_graphs([pos_dumps[-1], neg_dump])
            intersec1 = substract_intersections(pos_dumps, neg_dump,
                                                        intersec1, intersec2)

            extract_diff_graph(pos_dumps[-1], intersec1)
            print('Changed:', len(intersec1[0]))
            services.print_collection(intersec1[2])
            services.print_collection(intersec1[0])
            print('Removed:', len(intersec1[1]))
            services.print_collection(intersec1[1])
            print('Added:', len(intersec1[2]))
    else:
        pass
    #  method to diff whole dump
#         if ndump is not None:
#             neg_dump = reader.read_memory_dump(ndump)


if __name__ == '__main__':
    status = main()
    sys.exit(status)
