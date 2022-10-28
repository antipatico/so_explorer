#!/usr/bin/env python3

import sys
import os.path
import os
from subprocess import Popen, PIPE, DEVNULL
from Crypto.Hash import SHA256
import argparse
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, func
from sqlalchemy.orm import sessionmaker, relationship

import web_interface

default_db_file = "explore.db"

Base = declarative_base()
Session = sessionmaker()

class SoFile(Base):
	__tablename__ = "sofiles"
	id = Column(Integer, primary_key=True)
	filename = Column(String, index=True)
	path = Column(String)
	hash = Column(String(32), index=True)

class Symbol(Base):
	__tablename__ = "symbols"
	id = Column(Integer, primary_key = True)
	sofile_id = Column(Integer, ForeignKey("sofiles.id"))
	sofile = relationship("SoFile", back_populates="symbols")
	name = Column(String, index=True)
	s_type = Column(String(1))

SoFile.symbols = relationship("Symbol", order_by=Symbol.id, back_populates="sofile")

def symbols_summary(session, limit=1000):
	"""return list of symbols + how many times they're used"""
	rc = session.query(Symbol.name, Symbol.s_type, func.count(Symbol.s_type)).group_by(Symbol.name, Symbol.s_type).order_by(Symbol.name).limit(limit)
	return rc

def symbols_search(session, search, limit=1000):
	"""return list of symbols + how many times they're used from a search query"""
	search = "%" + search + "%"
	rc = session.query(Symbol.name, Symbol.s_type, func.count(Symbol.s_type)).filter(Symbol.name.like(search)).group_by(Symbol.name, Symbol.s_type).order_by(Symbol.name).limit(limit)
	return rc

def symbol_get(session, sym):
	rc = session.query(Symbol).filter(Symbol.name == sym)
	return rc

def sofile_get(session, id):
	rc = session.query(SoFile).filter(SoFile.id == id).first()
	return rc

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
		if addr != " " * 8:
			addr, stype, name = entry.split(" ", 2)
		else:
			#print("addr is empty")
			#print(addr)
			#print(entry.lstrip(" ").split(" ", 1))
			stype, name = entry.lstrip(" ").split(" ", 1)
		#stype = entry[9]
		#name = entry[11:]
		v = {"address":addr, "stype":stype, "name":name}
		print(v)
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

def is_elf_file(filename):
	with open(filename, "rb") as f:
		data = f.read(4)
		if data != b"\x7fELF":
			return False
		else:
			return True

def process_sofile(filename):
	if os.path.islink(filename):
		print("WARNING: file %s is a symlink"%(os.path.basename(filename)))
		return
	if not is_elf_file(filename):
		print("WARNING: file %s not ELF file"%(os.path.basename(filename)))
		return
	hash = hash_file(filename)
	result = session.query(SoFile).filter(SoFile.hash == hash).first()
	if result is not None:
		print("WARNING: file %s is already in db as %s"%(os.path.basename(filename), result.filename))
		return
	syms = read_symbols(filename)
	sofile = SoFile(filename=os.path.basename(filename), path=filename, hash=hash)
	session.add(sofile)
	for sym in syms:
		s = Symbol(sofile=sofile, name=sym["name"], s_type=sym["stype"])
		session.add(s)
	session.commit()

def init_sql(db_filename):
	global session
	engine = sqlalchemy.create_engine("sqlite:///" + db_filename)
	Base.metadata.create_all(engine)
	Session.configure(bind=engine)
	session = Session()

def main():
	parser = argparse.ArgumentParser(prog="so_explorer", description="Easily browse symbols from modules")
	parser.add_argument('-d', "--database", dest="db_file", help="database filename", default=default_db_file)
	subparsers = parser.add_subparsers(dest="action")
	build_parser = subparsers.add_parser("build", help="build or update a database")
	build_parser.add_argument('-r', "--recursive", help="scan ELF files recursively", action="store_true")
	build_parser.add_argument("files", type=str, nargs="+", help="files or directories to add to database")
	serve_parser = subparsers.add_parser("serve", help="start the web server")
	
	args = parser.parse_args()
	
	init_sql(args.db_file)
	print(args)
	if args.action == "build":
		if args.recursive:
			for d in args.files:
				for root, dirs, files in os.walk(d):
					for f in files:
						filename = root + os.sep + f
						process_sofile(filename)
		else:
			for f in args.files:
				process_sofile(f)
	elif args.action == "serve":
		web_interface.run(session)
	else:
		parser.print_help()
if __name__== "__main__":
	main()