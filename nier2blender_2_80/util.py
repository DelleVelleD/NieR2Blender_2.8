#encoding = utf-8
import os
import sys
import struct
import numpy as np
import random

def to_float(bs):
	return struct.unpack("<f", bs)[0]

def to_float16(bs):
	return float(np.frombuffer(bs, np.float16)[0])

def to_int(bs):
	return (int.from_bytes(bs, byteorder='little'))
	
def to_intB(bs):
	return (int.from_bytes(bs, byteorder='big'))

def to_string(bs, encoding = 'utf8'):
	return bs.split(b'\x00')[0].decode(encoding)
	
def to_pghalf(bs):
	C = FloatDecompressor(6,9,47)
	return C.decompress(struct.unpack("<H", bs)[0])

def create_dir(dirpath):
	if not os.path.exists(dirpath):
		os.makedirs(dirpath)

def print_class(obj):
	print ('\n'.join(sorted(['%s:\t%s ' % item for item in obj.__dict__.items() if item[0].find('Offset') < 0 or item[0].find('unknown') < 0 ])))
	print('\n')

def current_postion(fp):
	print(hex(fp.tell()))

def to_bytes(arg):
	if type(arg) == int:
		return struct.pack('<I', arg)
	if type(arg) == str:
		return struct.pack('<I', int(arg, 16))

def dds_number(dds_path):
	split_dds = dds_path.split('_')
	#print(split_dds)
	dds_num = split_dds[-1].split('.')
	#print(dds_num)
	return int(dds_num[0])

def find_files(dir_name,ext):
	filenameArray = []
	for dirpath,dirnames,filename in os.walk(dir_name):
		for file in filename:
			filename = "%s\%s"%(dirpath,file)
			#print(filename)
			if filename.find(ext) > -1:
				filenameArray.append(filename)
	return filenameArray

def random_identifier():
	identifier_decimal = random.randint(268435456,4294967295) #(10000000,ffffffff)
	identifier_hex = hex(identifier_decimal)
	return identifier_hex
	
def nullBytes(num): 
	return b"".join([b"\x00" for x in range(num)])

def to_1Byte(arg): #no negatives
	if type(arg) == int:
		if arg == 0:
			return nullBytes(1)
		elif arg < 0:
			return struct.pack('<B', 255)
		else:
			return struct.pack('<B', arg)
	if type(arg) == float:
		return struct.pack('<B', int(round((arg * 127 + 127))))
	
def to_2Byte(arg): 
	if type(arg) == float:
		return struct.pack('<h', np.float16(arg).view("int16"))
	if type(arg) == int:
		if arg == 0:
			return nullBytes(2)
		else:
			return struct.pack('<h', arg)

def to_4Byte(arg):
	if type(arg) == int:
		if arg == 0:
			return nullBytes(4)
		else:
			return struct.pack('<i', arg)
	if type(arg) == str:
		return arg.encode('utf-8')+nullBytes(1)
	if type(arg) == float:
		return struct.pack('<f', arg)
		

#thanks Phernost (stackoverflow), yoinked from lihaochen910, FloatDecompressor(6,9,47) for Nier
class FloatDecompressor(object):
	significandFBits = 23
	exponentFBits = 8
	biasF = 127
	exponentF = 0x7F800000
	significandF = 0x007fffff
	signF = 0x80000000
	signH = 0x8000

	def __init__(self, eHBits, sHBits, bH):
		self.exponentHBits = eHBits
		self.significandHBits = sHBits
		self.biasH = bH

		self.exponentH = ((1 << eHBits) - 1) << sHBits
		self.significandH = (1 << sHBits) - 1

		self.shiftSign = self.significandFBits + self.exponentFBits - \
			self.significandHBits - self.exponentHBits
		self.shiftBits = self.significandFBits - self.significandHBits

	def decompress(self, value):
		ui = value
		sign = ui & self.signH
		ui ^= sign

		sign <<= self.shiftSign
		exponent = ui & self.exponentH
		significand = ui ^ exponent
		significand <<= self.shiftBits

		si = sign | significand
		magic = 1.0
		if exponent == self.exponentH:
			si |= self.exponentF
		elif exponent != 0:
			exponent >>= self.significandHBits
			exponent += self.biasF - self.biasH
			exponent <<= self.significandFBits
			si |= exponent
		elif significand != 0:
			magic = (2 * self.biasF - self.biasH) << self.significandFBits
			magic = struct.unpack("f", struct.pack("I", magic))[0]
		f = struct.unpack("f", struct.pack("I", si))[0]
		f *= magic
		return f