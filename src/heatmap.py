#!/usr/bin/python
'''
Created on Oct 3, 2012

@author: David I. Urbina
'''
import matplotlib.pyplot as plt
import reader
import sys

if __name__ == '__main__':
	filename = sys.argv[1]

	md = reader.read_memory_dump(filename)

	freq = md.calculate_frequencies()

	plt.contourf(freq)
	plt.colorbar();
	plt.title(filename)
	plt.show()
# 	plt.savefig(filename + '.png')
