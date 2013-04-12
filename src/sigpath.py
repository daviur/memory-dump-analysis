#!/usr/bin/python
'''
Created on Mar 1, 2013

@author: David I Urbina
'''
from __future__ import print_function
from extras import reader, services
from finding_doi import memory_diffing, value_scanning
from signature_generation import extract_paths
import networkx as nx
import parts

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Generates a list of signature \
                                            paths to the data of interest')
    parser.add_argument('-p', required=True, nargs='+', dest='pos_dumps',
                    metavar='dump', help='list of positive memory dumps')
    parser.add_argument('-n', dest='neg_dump', metavar='dump',
                    help='negative memory dump')
    group = parser.add_argument_group('value scanning')
    group.add_argument('-v', nargs='+', dest='values', metavar='value',
                                    help="memory dumps' corresponding values")
    group.add_argument('-t', choices=['string', 'number'],
                                                    help='possible encodings')
    args = parser.parse_args()
    if args.values and not args.t:
        parser.error('Value scanning requires encoding')
    if args.values and len(args.pos_dumps) != len(args.values):
        parser.error('Different number of memory dumps and values')
    if len(args.pos_dumps) == 1 and not args.values:
        parser.error('Analysis of one memory dump requires a value')

    #===========================================================================
    # Memory Graph Generation
    #===========================================================================
    print('MEMORY GRAPH GENERATION')
    pos_dumps = [reader.read_memory_dump(f) for f in args.pos_dumps]
    for md in pos_dumps:
        md.build_memory_graph()
    if args.neg_dump:
        neg_dump = reader.read_memory_dump(args.neg_dump)
        neg_dump.build_memory_graph()

    # If only one positive memory dump
    graph = pos_dumps[-1].memory_graph
    graph.roots = pos_dumps[-1].modules

    #===========================================================================
    # Finding Data of Interest
    #===========================================================================
    print('FINDING DATA OF INTEREST')
    ocb = dict()  # Different offsets by Changing Buffer
    diffing = None  # (Different, Removed, Added) Buffers
    if len(pos_dumps) > 1:
    #--------------------------------------------- Memory Diffing at graph level
        print('\tDiffing memory graphs...', end='')
        diffing = memory_diffing.diff_memory_graphs(pos_dumps)

        if args.neg_dump:
            neg_diffing = memory_diffing.diff_memory_graphs([pos_dumps[-1],
                                                            neg_dump])
            diffing = memory_diffing.substract_intersections(pos_dumps, neg_dump,
                                                            diffing, neg_diffing)
        print('READY')
    #-------------------------------------------- Memory Diffing at buffer level
        print('\tDiffing buffers...', end='')
        for b in diffing[0].copy():
            ocb[b] = memory_diffing.diff_memory_segments_by_address(b.address,
                                                                        pos_dumps)
            # There is at least one common offset across dumps?
            if len(ocb[b]) == 0:
                del ocb[b]
                diffing[0].remove(b)
                continue

            if args.neg_dump:
                offsets = memory_diffing.diff_memory_segments_by_address(
                                        b.address, [pos_dumps[-1], neg_dump])
                ocb[b] = ocb[b] - offsets
# TODO: do we need ranges?
            # ocb[b] = services.extract_ranges(list(ocb[b]))

        print('READY')

        if len(pos_dumps) > 1:
            print('Changed:', len(diffing[0]))
            for b in diffing[0]:
                print(repr(b), '#different offsets:', len(ocb[b]))
            print('Removed:', len(diffing[1]))
            services.print_collection(diffing[1])
            print('Added:', len(diffing[2]))
            services.print_collection(diffing[2])

        for b in diffing[2]:
            ocb[b] = {0}

        # The graph resulting from the memory diffing
        graph = memory_diffing.create_diff_graph(pos_dumps[-1], diffing)
#         for (b, o) in ocb.items():
#             print(b, o)

    #------------------------------------------------------------ Value Scanning
    if args.values:
        print('\tValue Scanning...', end='')

        vob = dict()  # Value offset by buffer
        # Only one memory dump?
        if diffing == None:  # Yes, use graph
            vob = value_scanning.offsets_in_graph(graph, args.t, args.values[0])
        else:  # No, use diffing
            vob = value_scanning.offsets_in_diffing(pos_dumps, args.values,
                                                                diffing, args.t)
#         for (b, o) in vob.items():
#             print(b, o)
        print('READY')
    #---------------------------- Intercepting Memory Diffing and Value Scanning

    fcob = dict()  # Final candidate offsets by buffer
    # Memory Diffing and Value Scanning
    if len(pos_dumps) > 1 and args.values:
        print('\tIntercepting Memory Diffing and Value Scanning...')
        for b in diffing[0]:
            offsets = ocb[b] & {o[0] for o in vob[b]}
            if len(offsets) > 0:
                fcob[b] = offsets
        for b in diffing[2]:
            offsets = {o[0] for o in vob[b]}
            if len(offsets) > 0:
                fcob[b] = offsets
    # Only Memory Diffing
    elif len(pos_dumps) > 1:
        fcob = ocb
    # Only Value Scanning
    else:
        for (b, l) in vob.items():
            if len(l) > 0:
                of = {o[0] for o in l}
                fcob[b] = of

    print('\tFinal set of candidate offsets:', len(fcob))
    for (b, o) in fcob.items():
        print('\t\t', b, o)

    #===========================================================================
    # Signature Generation
    #===========================================================================
    print('SIGNATURE GENERATION')
    #------------------------------------------------------------- Extract Paths

    print('\tExtracting Paths...', end='')
    pb = dict()  # Paths by buffer
    for b in fcob.keys():
        pb[b] = extract_paths.by_buffer(graph, b)
    print('READY')
    for (b, paths) in pb.items():
        print('\t', b)
        for i in xrange(len(paths)):
            n = paths[i].normalize()
            nx.write_dot(n, str(b) + '-' + str(i) + '.dot')
            print('\t\t', i, '-', paths[i])
#             print('\t\t', i, '-', str(n))




