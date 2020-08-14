#!/usr/bin/env python3

import sys
from subprocess import Popen, PIPE, DEVNULL
from Crypto.Hash import SHA256

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

def hash_file(filename):
	h = SHA256.new()
	with open(filename, "rb") as f:
		while True:
			buf = f.read(4096)
			if len(buf) == 0:
				break
			h.update(buf)
	return h.hexdigest()

def main(args):
	read_symbols(args[1])
	print(hash_file(args[1]))

if __name__== "__main__":
	main(sys.argv)