#!/usr/bin/python
'''
Created on Dec 13, 2012

@author: David I. Urbina
'''
from __future__ import print_function
import argparse
import extras.reader as reader
import finding_doi.memory_diffing as diffing
import finding_doi.value_scanning as scanning

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compares memory dumps data structures')
    parser.add_argument(dest='address' , metavar='address', help='address of the data structure to compare.')
    parser.add_argument(dest='dumps', nargs='+', metavar='dumps', help='memory dump files.')
    parser.add_argument('-r', dest='dump', metavar='dump', help='memory dump to remove.')
    args = parser.parse_args()

    memory_dumps = [reader.read_memory_dump(f) for f in args.dumps]

    for md in memory_dumps:
        md.build_memory_graph()

    dss = list()
    for md in memory_dumps:
        for m in md.modules:
            if m.address == int(args.address, 16):
                dss.append(m)
                break

    if len(dss) == 0:
        dss = [md.data_structures[int(args.address, 16)] for md in memory_dumps]

    offsets1 = diffing.diff_memory_segments(dss)

    # Diffing the negative dump
    if args.dump != None:
        dump = reader.read_memory_dump(args.dump)
        dump.build_memory_graph()
        dss2 = list()
        for m in memory_dumps[-1].modules:
            if m.address == int(args.address, 16):
                dss2.append(m)
                break
        for m in dump.modules:
            if m.address == int(args.address, 16):
                dss2.append(m)
                break
        if len(dss2) == 0:
            dss2 = [memory_dumps[-1].data_structures[int(args.address, 16)], dump.data_structures[int(args.address, 16)]]
        offsets2 = diffing.diff_memory_segments(dss2)
        # Substracting the negative diffing
        offsets1 = offsets1 - offsets2

    print("Different offsets:", len(offsets1))
    for o in offsets1:
#         print(o)
        print('Offset:', o)
        for (md, b) in zip(memory_dumps, dss):
            print('\t', md.name, '-', '0x{:x}'.format(b.address))
            for (t, v) in scanning.get_possible_values(b, o):
                print('\t\t{:7} {}'.format(t, v))

#     diffing.draw_segments_diffing(dss, offsets1)
