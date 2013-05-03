#!/usr/bin/env python
'''
Created on Oct 3, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from parts import ReferencePath
import argparse
import extras.reader as reader
import networkx as nx

# search_paths = nx.all_shortest_paths
search_paths = nx.all_simple_paths


def _build_reference_paths(G, paths, offset=None, data=None):
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
# TODO: Avoid Private Data
#         if isinstance(n, PrivateData):
#             continue
        for o in n.string_offset(ascii):
            paths = list()
            for m in md.modules:
                try:
                    paths.extend(search_paths(G, m, n))
                except nx.NetworkXNoPath:
                    continue
            rps.extend(_build_reference_paths(G, paths, o, ascii))
    return rps


def by_address(memory_dump, address):
    # Address corresponds to a module?
    b = next((m for m in memory_dump.modules if m.address == address), None)
    # if not, does it correspond to a data structure?
    if b == None:
        b = md.data_structures.get(address)
    # if neither, return empty list
    if b == None:
        return []

    paths = list()
    G = memory_dump.memory_graph
    for m in memory_dump.modules:
        try:
            paths.extend(search_paths(G, m, b))
        except nx.NetworkXNoPath:
            pass
    return _build_reference_paths(G, paths)


def by_buffer(graph, buff):
    paths = list()
    for m in graph.roots:
        if m == buff:
            paths.append([m])
        try:
            paths.extend(search_paths(graph, m, buff))
        except nx.NetworkXNoPath:
            pass
    return _build_reference_paths(graph, paths)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List the possible \
        reference paths to the specified data structure in a memory \
        dump. The data structure may be specified by its value or by \
        its address. By default it search for shortest reference paths.')
    parser.add_argument(dest='dump', metavar='dump', help='memory dump file.')
    parser.add_argument('-a', dest='address', metavar='address',
                                        help='address of the data structure.')
    parser.add_argument('-s', dest='ascii', metavar='ascii',
                                            help='ASCII value to search for.')
    parser.add_argument('-u', dest='unicode', metavar='unicode',
                                    help='Unicode(UTF16) value to search for.')
    parser.add_argument('--All', dest='all', action='store_true',
                help='search for all simple paths. It may take a long time.')
    args = parser.parse_args()

    md = reader.read_memory_dump(args.dump)
    md.build_memory_graph()

    if args.all:
        search_paths = nx.all_simple_paths

    # Search by address
    if args.address != None:
        rps = by_address(md, int(args.address, 16))
        print('{} paths to data structure 0x{:x}'.format(len(rps),
                                                     int(args.address, 16)))
    # Search by ASCII
    elif args.ascii != None:
        rps = by_string(md, args.ascii)
        print('{} paths to the ASCII string {}'.format(len(rps), args.ascii))
    # Search by Unicode(UTF16)
    elif args.unicode != None:
#         rps = by_string(md, args.unicode.encode('utf16'))
        rps = by_string(md, unicode(args.unicode, 'utf16'))
        print('{} paths to the Unicode(UTF16) string {}'.format(len(rps),
                                                                args.unicode))

    for i, rp in zip(xrange(len(rps)), sorted(rps, key=lambda rp:
                                                                str(rp.root))):
        print(i, '-', rp)
        nx.write_dot(rps[i].normalize(), '{}-nrp{}.dot'.format(md.name, i))
