#!/usr/bin/env python
#coding:utf-8
# Author:  David I. Urbina
# Purpose: writer of memorydump files
# Created: 01/22/2013


def write_memory_dump_data(filename, data):
    with open(filename, 'wb') as f:
        f.write(data)

