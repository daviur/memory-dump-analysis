'''
Created on Dec 13, 2012

@author: David I. Urbina
'''
from __future__ import print_function
import MemoryDumpDiffing
import MemoryDumpReader
import MemoryDumpValueFindding
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compares memory dumps data structures')
    parser.add_argument('-d', dest='address' , metavar='address', help='address of the data structure to compare.')
    parser.add_argument(dest='filename' , metavar='memorydump', help='the file name of the memory dump.')
    parser.add_argument(dest='filenames' , nargs='+', metavar='other', help='other files.')
    args = parser.parse_args()

    md1 = MemoryDumpReader.read_memory_dump(args.filename)
    memory_dumps = [md1]
    for f in args.filenames:
        md = MemoryDumpReader.read_memory_dump(f)
        memory_dumps.append(md)

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

    offsets = MemoryDumpDiffing.diff_memory_segments(dss)
    print("Different offsets:", len(offsets))
    for o in offsets:
        print('Offset:', o)
        for (md, ds) in zip(memory_dumps, dss):
            print('\t', md.name, '-', '0x{:x}'.format(ds.address))
            for (t, v) in MemoryDumpValueFindding.get_possible_values(ds, o):
                print('\t\t{:7} {}'.format(t, v))

    MemoryDumpDiffing.draw_segments_diffing(dss, offsets)

