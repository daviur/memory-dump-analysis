#!/usr/bin/python
'''
Created on Nov 26, 2012

@author: David I. Urbina
'''
from __future__ import print_function
from minidump_scanning.minidump import *
import argparse

# Modules to exclude
# _STDLIB_EXC_ = []
_STDLIB_EXC_ = ['rpcrt4.dll', 'ole32.dll', 'advapi32.dll', 'user32.dll', 'comctl32.dll',
 				'winmm.dll', 'secur32.dll', 'gdi32.dll', 'gdiplus.dll', 'wininet.dll',
 				'crypt32.dll', 'msasn1.dll', 'oleaut32.dll', 'shlwapi.dll', 'comdlg32.dll',
 				'shell32.dll', 'winspool.drv', 'oledlg.dll', 'version.dll', 'riched32.dll',
 				'riched20.dll', 'rsaenh.dll', 'clbcatq.dll', 'comres.dll', 'shdocvw.dll',
 				'cryptui.dll', 'netapi32.dll', 'wintrust.dll', 'imagehlp.dll', 'wldap32.dll',
 				'uxtheme.dll', 'xpsp2res.dll', 'wtsapi32.dll', 'winsta.dll', 'imm32.dll',
 				'msimg32.dll', 'apphelp.dll', 'ws2_32.dll', 'ws2help.dll', 'urlmon.dll',
 				'setupapi.dll', 'msacm32.dll', 'sensapi.dll', 'oleacc.dll', 'iphlpapi.dll',
 				'wsock32.dll', 'msls31.dl', 'psapi.dll', 'sxs.dll', 'mlang.dll', 'simtf.dll',
 				'rasapi32.dll', 'rasman.dll', 'tapi32.dll', 'rtutils.dll', 'shdoclc.dll',
 				'jscript.dll', 'mswsock.dll', 'hnetcfg.dll', 'wshtcpip.dll', 'dnsapi.dll',
 				'winrnr.dll', 'rasadhlp.dll', 'schannel.dll', 'userenv.dll', 'dssenh.dll',
 				'perfos.dll', 'wdmaud.drv', 'msacm32.drv', 'midimap.dll', 'msvcr100.dll',
 				'msvcp100.dll', 'kernel32.dll', 'msvcrt.dll', 'ntdll.dll', 'mshtml.dll',
 				'msctf.dll']

# Modules to include
_STDLIB_INCL_ = ['kernel32.dll', 'msvcrt.dll', 'ntdll.dll', 'mshtml.dll', 'msctf.dll']

#
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




def extract_modules(filename, minidump, all_mod):
	for s in minidump.MINIDUMP_DIRECTORY.value:
		if s.StreamType == 'ModuleListStream':
			print('Extracting modules...', end=' ')
			with open(filename.replace('dmp', 'modules'), 'w') as f:
				for m in s.DirectoryData.MINIDUMP_MODULE:
					if not all_mod and any(x in m.ModuleName.lower() for x in _STDLIB_EXC_):
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
