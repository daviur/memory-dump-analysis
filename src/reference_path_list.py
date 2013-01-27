'''
Created on Oct 3, 2012

@author: David I. Urbina
'''
from __future__ import print_function
import reader
import argparse
import networkx as nx

def list_reference_path(memory_dump, data_structure):
    
    shortest_paths = list()
    
    G = memory_dump.memory_graph
    for m in memory_dump.modules:        
        try:
            for p in nx.all_shortest_paths(G, m, data_structure):                
                shortest_paths.append(p)
        except nx.NetworkXNoPath:
            pass

    #rps = list()
    #for p in shortest_paths:
        #if len(p) == 1:
            #rps.append("<p a=0x{:x} o=[]>".format(p[0].address))            
        #else:
            #address = p[0].address + G[p[0]][p[1]]['label']            
            #offsets = list()
            #if len(p) > 2:
                #for i in xrange(1, len(p) - 1):
                    #offsets.append(G[p[i]][p[i + 1]]['label'])
            #rps.append("<p a=0x{:x} o={}>".format(address, offsets))
    #return rps
    
    rps = list()
    for p in shortest_paths:
        path = str(p[0])
        for i in xrange (len(p) - 1):
            path += '-<{}>->{}'.format(G[p[i]][p[i + 1]]['label'], str(p[i + 1]))
        rps.append(path)
    return rps


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List the possible reference path for a data structure in a memory dump.')
    parser.add_argument(dest='address' , metavar='address', help='address of the data structure.')
    parser.add_argument(dest='dump', metavar='dump', help='memory dump file.')
    args = parser.parse_args()
    
    md = reader.read_memory_dump(args.dump)    
    md.build_memory_graph()
    
    ds = None
    for m in md.modules:
        if m.address == int(args.address, 16):
            ds = m
            break

    if ds == None:
        ds = md.data_structures[int(args.address, 16)]
        
    rps = list_reference_path(md, ds)    
    print(('{} paths to data structure 0x{:x} '.format(len(rps), int(args.address, 16), 16)))    
    for p in rps:
        print(p)