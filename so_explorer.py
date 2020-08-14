#!/usr/bin/env python3

import sys
from subprocess import Popen, PIPE, DEVNULL

def read_symbols(filename):
	p = Popen(["/usr/bin/nm", "-D", "-C", filename], stdin=DEVNULL, stdout=PIPE, bufsize=2048)
	symbols = []
	while True:
		entry = p.stdout.readline()
		if entry == b'':
			break
		entry=str(entry.strip(b'\n'), 'utf-8')
		#print(entry)
		addr = entry[:8]
		stype = entry[9]
		name = entry[11:]
		v = {"address":addr, "stype":stype, "name":name}
		#print(v)
		symbols.append(v)
	return symbols



def main(args):
	read_symbols(args[1])

if __name__== "__main__":
	main(sys.argv)