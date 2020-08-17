#!/usr/bin/env python3

import sys
import os.path
from subprocess import Popen, PIPE, DEVNULL
from Crypto.Hash import SHA256
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship

db_file = "explore.db"

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

def process_sofile(filename):
	hash = hash_file(filename)
	result = session.query(SoFile).filter(SoFile.hash == hash).first()
	if result is not None:
		print("file %s is already in db as %s"%(os.path.basename(filename), result.filename))
		return
	syms = read_symbols(filename)
	sofile = SoFile(filename=os.path.basename(filename), path=filename, hash=hash)
	session.add(sofile)
	for sym in syms:
		s = Symbol(sofile=sofile, name=sym["name"], s_type=sym["stype"])
		session.add(s)
	session.commit()

def main(args):
	global session
	engine = sqlalchemy.create_engine("sqlite:///" + db_file, echo=True)
	Base.metadata.create_all(engine)
	Session.configure(bind=engine)
	session = Session()
	process_sofile(args[1])

if __name__== "__main__":
	main(sys.argv)