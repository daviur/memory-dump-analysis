#!/usr/bin/env python
'''
Created on Mar 1, 2013

@author: David I Urbina
'''
from __future__ import print_function
from extras import reader, services
from finding_doi import memory_diffing, value_scanning
from signature_generation import extract_paths
import argparse
import networkx as nx
import sys


def process_command_line(argv):
    '''
    Return a 4-tuple: (positive dumps, negative dump, values, type).
    "argv" is a list of arguments, or "None" for "sys.argv[1:]".
    '''
    if argv is None:
        argv = sys.argv[1:]

    # initializing the parser object
    parser = argparse.ArgumentParser(description='Generates a list of \
                                    signature paths to the data of interest')
    # defining command options
    parser.add_argument('-p', required=True, nargs='+', dest='pos_dumps',
                    metavar='dump', help='list of positive memory dumps')
    parser.add_argument('-n', dest='neg_dump', metavar='dump',
                    help='negative memory dump')
    group = parser.add_argument_group('value scanning')
    group.add_argument('-v', nargs='+', dest='values', metavar='value',
                                    help="memory dumps' corresponding values")
    group.add_argument('-t', dest='type', choices=['string', 'number'],
                                                    help='possible encodings')
    # checking arguments
    args = parser.parse_args(argv)
    if args.values and not args.type:
        parser.error('Value scanning requires encoding')
    if args.values and len(args.pos_dumps) != len(args.values):
        parser.error('Different number of memory dumps and values')
    if len(args.pos_dumps) == 1 and not args.values:
        parser.error('Analysis of one memory dump requires a value')
    return args.pos_dumps, args.neg_dump, args.values, args.type


def main(argv=None):
    pdump, ndump, values, _type = process_command_line(argv)

    #==========================================================================
    # Memory Graph Generation
    #==========================================================================
    print('MEMORY GRAPH GENERATION')
    pos_dumps = [reader.read_memory_dump(f) for f in pdump]
    for md in pos_dumps:
        md.build_memory_graph()
    if ndump:
        neg_dump = reader.read_memory_dump(ndump)
        neg_dump.build_memory_graph()

    # If only one positive memory dump
    graph = pos_dumps[-1].memory_graph
    graph.roots = pos_dumps[-1].modules

    #==========================================================================
    # Finding Data of Interest
    #==========================================================================
    print('FINDING DATA OF INTEREST')
    obb = dict()  # Offsets by Buffer
    diffing = None  # (Different, Removed, Added) Buffers
    if len(pos_dumps) > 1:
    #-------------------------------------------- Memory Diffing at graph level
        services.start_op('\tDiffing memory graphs...')

        diffing = memory_diffing.diff_memory_graphs(pos_dumps)

        if ndump:
            neg_diffing = memory_diffing.diff_memory_graphs([pos_dumps[-1],
                                                            neg_dump])
            diffing = memory_diffing.substract_intersections(pos_dumps,
                             [pos_dumps[-1], neg_dump], diffing, neg_diffing)

        services.end_op()
    #------------------------------------------- Memory Diffing at buffer level
        services.start_op('\tDiffing buffers...')
        for b in diffing[0].copy():
            obb[b] = memory_diffing.diff_memory_segments_by_address(b.address,
                                                                     pos_dumps)
            # There is at least one common offset across dumps?
            if len(obb[b]) == 0:
                del obb[b]
                diffing[0].remove(b)
                continue

            if ndump:
                offsets = memory_diffing.diff_memory_segments_by_address(
                                        b.address, [pos_dumps[-1], neg_dump])
                obb[b] = obb[b] - offsets
# TODO: do we need ranges?
            # obb[b] = services.extract_ranges(list(obb[b]))

        services.end_op()

        if len(pos_dumps) > 1:
            print('Changed:', len(diffing[0]))
            for b in diffing[0]:
                print(repr(b), '#different offsets:', len(obb[b]))
            print('Removed:', len(diffing[1]))
            services.print_collection(diffing[1])
            print('Added:', len(diffing[2]))
            services.print_collection(diffing[2])

        # Adding the added buffers with offset 0
        for b in diffing[2]:
            obb[b] = {0}

        # The graph resulting from the memory diffing
        services.start_op('Extracting diff_graph...')
        graph = memory_diffing.extract_diff_graph(pos_dumps[-1], diffing)
        services.end_op()
#         for (b, o) in obb.items():
#             print(b, o)

# TODO: remove
        return 1

    #----------------------------------------------------------- Value Scanning
    if values:
        services.start_op('\tValue Scanning...')
        obbbv = dict()  # Offsets by buffer by value
        # Only one memory dump?
        if diffing == None:  # Yes, use graph
            obbbv = value_scanning.offsets_in_graph(graph, _type,
                                                                values[0])
        else:  # No, use diffing
            obbbv = value_scanning.offsets_in_diffing(pos_dumps, values,
                                                            diffing, _type)
#         for (b, o) in obbbv.items():
#             print(b, o)
        services.end_op()
    #--------------------------- Intercepting Memory Diffing and Value Scanning

    fcob = dict()  # Final candidate offsets by buffer
    # Memory Diffing and Value Scanning
    if len(pos_dumps) > 1 and values:
        services.start_op('\tIntercepting Memory Diffing and Value \
                                                                Scanning...')
        for b in diffing[0]:  # Intercept changed with values
            offsets = obb[b] & {o[0] for o in obbbv[b]}
            if len(offsets) > 0:
                fcob[b] = offsets
        for b in diffing[2]:  # Intercept added with values
            offsets = {o[0] for o in obbbv[b]}
            if len(offsets) > 0:
                fcob[b] = offsets
        services.end_op()
    # Only Memory Diffing
    elif len(pos_dumps) > 1:
        fcob = obb
    # Only Value Scanning
    else:
        for (b, l) in obbbv.items():
            if len(l) > 0:
                of = {o[0] for o in l}
                fcob[b] = of

    print('\tFinal set of candidate offsets:', len(fcob))
    for (b, o) in fcob.items():
        print('\t\t', b, o)

    #==========================================================================
    # Signature Generation
    #==========================================================================
    print('SIGNATURE GENERATION')
    #------------------------------------------------------------ Extract Paths

    services.start_op('\tExtracting Paths...')
    pb = dict()  # Paths by buffer
    for b in fcob:
        pb[b] = extract_paths.by_buffer(graph, b)
    services.end_op()

    for (b, paths) in pb.items():
        print('\t', b)
        for (index, path) in enumerate(paths):
            n = path.normalize()
            nx.write_dot(n, str(b) + '-' + str(index) + '.dot')
            print('\t\t', index, '-', path)
#             print('\t\t', index, '-', str(n))
    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)
