#!/usr/bin/python
'''
Created on Nov 26, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from Minidump import *
import argparse


def extract_memory(filename, minidump):
    with open(filename, 'rb') as f:
        for s in minidump.MINIDUMP_DIRECTORY.value:
            if s.StreamType == 'Memory64ListStream':
                print('Extracting memory...', end=' ')
                with open(filename.replace('dmp', 'core'), 'w') as f2:
                    f2.write(f.read()[s.DirectoryData.BaseRva:])
                print('DONE')
                return


def extract_segments(filename, minidump):
    for s in minidump.MINIDUMP_DIRECTORY.value:
        if s.StreamType == 'Memory64ListStream':
            print('Extracting segments...', end=' ')
            with open(filename.replace('dmp', 'segments'), 'w') as f:
                for d in s.DirectoryData.MINIDUMP_MEMORY_DESCRIPTOR64.value:
                    value = '{:x}:{:x}\n'.format(d.StartOfMemoryRange, d.DataSize)
                    f.write(value)
            print('DONE')
            return


def is_standard_module(name):
    return 'windows' in name.lower()


def extract_modules(filename, minidump, all_mod):
    for s in minidump.MINIDUMP_DIRECTORY.value:
        if s.StreamType == 'ModuleListStream':
            print('Extracting modules...', end=' ')
            with open(filename.replace('dmp', 'modules'), 'w') as f:
                for m in s.DirectoryData.MINIDUMP_MODULE:
                    if not all_mod and is_standard_module(m.ModuleName):
                        continue
                    name = m.ModuleName.split('\\')[-1]
                    value = '{:x}:{:x}:{}\n'.format(m.BaseOfImage, m.SizeOfImage, name)
                    f.write(value)
            print('DONE')
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse a minidump file.')
    parser.add_argument(dest='filename' , metavar='filename', help='the file name of the memory dump.')
    parser.add_argument('-m', dest='modules', action='store_true', help='extract not-standard modules to "filename.modules" file.')
    parser.add_argument('-M', dest='all_modules', action='store_true', help='extract all modules to "filename.modules" file.')
    parser.add_argument('-s', dest='segments', action='store_true', help='extract segments to "filename.segments" file.')
    parser.add_argument('-c', dest='core', action='store_true', help='extract memory to "filename.core" file.')
    args = parser.parse_args()

    minidump = MINIDUMP_HEADER.parse_stream(open(args.filename))
    print('MINIDUMP_HEADER')
    print(minidump)

    if args.core:
        extract_memory(args.filename, minidump)

    if args.segments:
        extract_segments(args.filename, minidump)

    if args.modules or args.all_modules:
        extract_modules(args.filename, minidump, args.all_modules)
