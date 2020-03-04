#t might be different, t = (frameIndex-values[0].index) / (values[-1].index-values[0].index)
from nier2blender_2_80.util import *

class mot_record(object):
	def __init__(self, mot_file):
		super(mot_record, self).__init__()
		self.offset = mot_file.tell()
		self.bone_id = to_int(mot_file.read(2))
		self.valueType = to_int(mot_file.read(1)) #0-2 translationXYZ, 3-5 rotationXYZ, 7-9 scalingXYZ
		self.recordType = to_int(mot_file.read(1))
		self.valueCount = to_int(mot_file.read(2))
		self.unknown1 = to_int(mot_file.read(2))
		
		if self.recordType == 0:
			self.final4 = to_float(mot_file.read(4)) #the value
			self.values_header = None
		else:
			self.final4 = to_int(mot_file.read(4)) #offset for values = this + this record offset
			mot_file.seek(self.offset + self.final4)
			self.values_header = mot_values_header(mot_file, self.recordType, self.valueCount)
			
			
	def get_frame(self, frameIndex):
		if self.recordType == 0: #Type 0 --------------------------------------
			return self.final4
		else:
			values = self.values_header.values
			if self.recordType == 1: #Type 1 --------------------------------------
				if(frameIndex < 0):
					return values[0].p
				elif(frameIndex > len(values)):
					return values[-1].p
				else:
					return values[frameIndex].p
			elif 2 <= self.recordType <= 3: #Type 2/3 --------------------------------------
				if(frameIndex < 0):
					return self.values_header.p + self.values_header.dp * values[0].cp
				elif(frameIndex > len(values)):
					return self.values_header.p + self.values_header.dp * values[-1].cp
				else:
					return self.values_header.p + self.values_header.dp * values[frameIndex].cp
			elif self.recordType == 4: #Type 4 --------------------------------------
				if(frameIndex <= values[0].frameIndex):
					return values[0].p
				if(frameIndex >= values[-1].frameIndex):
					return values[-1].frameIndex
				
				p_i = 0
				for i, value in enumerate(values):
					if frameIndex < value.frameIndex:
						p_i = i-1
						break
					if frameIndex == value.frameIndex:
						return value.p
				
				k1 = values[p_i]
				k2 = values[p_i + 1]
				
				p0 = k1.p
				m0 = k1.m1
				p1 = k2.p
				m1 = k2.m0
				t = 1.0 * (frameIndex - k1.frameIndex)/(k2.frameIndex - k1.frameIndex)
				val = (2*t*t*t - 3*t*t + 1)*p0 + (t*t*t - 2*t*t + t)*m0 + (-2*t*t*t + 3*t*t)*p1 + (t*t*t - t*t)*m1
				return val
					
				print('[MOT-Error] Record frame outside bounds. boneNumber: %d, recordType: %d, frameIndex: %d, minBound: %d, maxBound: %d' % (self.bone_id, self.recordType, frameIndex, k1.frameIndex, k2.frameIndex))
			
#				if(frameIndex < 0):
#					return values[0].p
#				elif(frameIndex > len(values)):
#					return values[-1].p
#				else:
#					for i in range(1, len(values)):
#						if(frameIndex == values[i-1].frameIndex):
#							return values[i-1].p
#						elif(frameIndex == values[i].frameIndex):
#							return values[i].p
#						elif(values[i-1].frameIndex < frameIndex < values[i].frameIndex):
#							p0 = values[i-1].p
#							m0 = values[i-1].m1
#							p1 = values[i].p
#							m1 = values[i].m0
#							t = 1.0 * (frameIndex-values[i-1].frameIndex)/(values[i].frameIndex - values[i-1].frameIndex)
#							val = (2*t*t*t - 3*t*t + 1)*p0 + (t*t*t - 2*t*t + t)*m0 + (-2*t*t*t + 3*t*t)*p1 + (t*t*t - t*t)*m1
#							return val
#						else:
#							print('[MOT-Error] Record frame outside bounds. boneNumber: %d, recordType: %d, frameIndex: %d, minBound: %d, maxBound: %d' % (self.bone_id, self.recordType, frameIndex, values[i-1].frameIndex, values[i].frameIndex))
			elif 5 <= self.recordType <= 6: #Type 5/6 --------------------------------------
				if(frameIndex <= values[0].frameIndex):
					return self.values_header.p + self.values_header.dp * values[0].cp
				if(frameIndex >= values[-1].frameIndex):
					return self.values_header.p + self.values_header.dp * values[-1].cp
				
				p_i = 0
				for i, value in enumerate(values):
					if frameIndex < value.frameIndex:
						p_i = i-1
						break
					if frameIndex == value.frameIndex:
						return self.values_header.p + self.values_header.dp * value.cp
				
				k1 = values[p_i]
				k2 = values[p_i + 1]
				
				p0 = self.values_header.p + self.values_header.dp * k1.cp
				m0 = self.values_header.m1 + self.values_header.dm1 * k1.cm1
				p1 = self.values_header.p + self.values_header.dp * k2.cp
				m1 = self.values_header.m0 + self.values_header.dm0 * k1.cm0
				t = 1.0 * (frameIndex - k1.frameIndex)/(k2.frameIndex - k1.frameIndex)
				val = (2*t*t*t - 3*t*t + 1)*p0 + (t*t*t - 2*t*t + t)*m0 + (-2*t*t*t + 3*t*t)*p1 + (t*t*t - t*t)*m1
				return val
					
				print('[MOT-Error] Record frame outside bounds. boneNumber: %d, recordType: %d, frameIndex: %d, minBound: %d, maxBound: %d' % (self.bone_id, self.recordType, frameIndex, k1.frameIndex, k2.frameIndex))
					
#				if(frameIndex < 0):
#					return self.values_header.p + self.values_header.dp * values[0].cp
#				elif(frameIndex > len(values)):
#					return self.values_header.p + self.values_header.dp * values[-1].cp
#				else:
#					for i in range(1, len(values)):
#						if(frameIndex == values[i-1].frameIndex):
#							return self.values_header.p + self.values_header.dp * values[i-1].cp
#						elif(frameIndex == values[i].frameIndex):
#							return self.values_header.p + self.values_header.dp * values[i].cp
#						elif(values[i-1].frameIndex < frameIndex < values[i].frameIndex):
#							p0 = self.values_header.p + self.values_header.dp * values[i-1].cp
#							m0 = self.values_header.m1 + self.values_header.dm1 * values[i-1].cm1
#							p1 = self.values_header.p + self.values_header.dp * values[i].cp
#							m1 = self.values_header.m0 + self.values_header.dm0 * values[i-1].cm0
#							t = 1.0 * (frameIndex - values[i-1].frameIndex)/(values[i].frameIndex - values[i-1].frameIndex)
#							val = (2*t*t*t - 3*t*t + 1)*p0 + (t*t*t - 2*t*t + t)*m0 + (-2*t*t*t + 3*t*t)*p1 + (t*t*t - t*t)*m1
#							return val
#						else:
#							print('[MOT-Error] Record frame outside bounds. boneNumber: %d, recordType: %d, frameIndex: %d, minBound: %d, maxBound: %d' % (self.bone_id, self.recordType, frameIndex, values[i-1].frameIndex, values[i].frameIndex))
			elif self.recordType == 7: #Type 7 --------------------------------------
				if(frameIndex <= values[0].frameIndex):
					return self.values_header.p + self.values_header.dp * values[0].cp
				if(frameIndex >= values[-1].frameIndex):
					return self.values_header.p + self.values_header.dp * values[-1].cp
				
				p_i = 0
				for i, value in enumerate(values):
					if frameIndex < value.frameIndex:
						p_i = i-1
						break
					if frameIndex == value.frameIndex:
						return self.values_header.p + self.values_header.dp * value.cp
				
				k1 = values[p_i]
				k2 = values[p_i + 1]
				
				p0 = self.values_header.p + self.values_header.dp * k1.cp
				m0 = self.values_header.m1 + self.values_header.dm1 * k1.cm1
				p1 = self.values_header.p + self.values_header.dp * k2.cp
				m1 = self.values_header.m0 + self.values_header.dm0 * k1.cm0
				t = 1.0 * (frameIndex - (frameIndex-1))/(((frameIndex-1) + k2.frameIndex) - (frameIndex-1))
				val = (2*t*t*t - 3*t*t + 1)*p0 + (t*t*t - 2*t*t + t)*m0 + (-2*t*t*t + 3*t*t)*p1 + (t*t*t - t*t)*m1
				return val
					
				print('[MOT-Error] Record frame outside bounds. boneNumber: %d, recordType: %d, frameIndex: %d, minBound: %d, maxBound: %d' % (self.bone_id, self.recordType, frameIndex, k1.frameIndex, k2.frameIndex))
			
#				if(frameIndex < 0):
#					return self.values_header.p + self.values_header.dp * values[0].cp
#				elif(frameIndex > len(values)):
#					return self.values_header.p + self.values_header.dp * values[-1].cp
#				else:
#					for i in range(1, len(values)):
#						if(frameIndex == values[i-1].frameIndex):
#							return self.values_header.p + self.values_header.dp * values[i-1].cp
#						elif(frameIndex == values[i].frameIndex):
#							return self.values_header.p + self.values_header.dp * values[i].cp
#						elif(values[i-1].frameIndex < frameIndex < values[i].frameIndex):
#							p0 = self.values_header.p + self.values_header.dp * values[i-1].cp
#							m0 = self.values_header.m1 + self.values_header.dm1 * values[i-1].cm1
#							p1 = self.values_header.p + self.values_header.dp * values[i].cp
#							m1 = self.values_header.m0 + self.values_header.dm0 * values[i-1].cm0
#							t = 1.0 * (frameIndex - (frameIndex-1))/(((frameIndex-1) + values[i].frameIndex) - (frameIndex-1))
#							val = (2*t*t*t - 3*t*t + 1)*p0 + (t*t*t - 2*t*t + t)*m0 + (-2*t*t*t + 3*t*t)*p1 + (t*t*t - t*t)*m1
#							return val
#						else:
#							print('[MOT-Error] Record frame outside bounds. boneNumber: %d, recordType: %d, frameIndex: %d, minBound: %d, maxBound: %d' % (self.bone_id, self.recordType, frameIndex, values[i-1].frameIndex, values[i].frameIndex))
			elif self.recordType == 8: #Type 8 --------------------------------------
				if(frameIndex <= values[0].frameIndex):
					return self.values_header.p + self.values_header.dp * values[0].cp
				if(frameIndex >= values[-1].frameIndex):
					return self.values_header.p + self.values_header.dp * values[-1].cp
				
				p_i = 0
				for i, value in enumerate(values):
					if frameIndex < value.frameIndex:
						p_i = i-1
						break
					if frameIndex == value.frameIndex:
						return self.values_header.p + self.values_header.dp * value.cp
				
				k1 = values[p_i]
				k2 = values[p_i + 1]
				
				p0 = self.values_header.p + self.values_header.dp * k1.cp
				m0 = self.values_header.m1 + self.values_header.dm1 * k1.cm1
				p1 = self.values_header.p + self.values_header.dp * k2.cp
				m1 = self.values_header.m0 + self.values_header.dm0 * k1.cm0
				t = 1.0 * (frameIndex - k1.frameIndex)/(k2.frameIndex - k1.frameIndex)
				val = (2*t*t*t - 3*t*t + 1)*p0 + (t*t*t - 2*t*t + t)*m0 + (-2*t*t*t + 3*t*t)*p1 + (t*t*t - t*t)*m1
				return val
					
				print('[MOT-Error] Record frame outside bounds. boneNumber: %d, recordType: %d, frameIndex: %d, minBound: %d, maxBound: %d' % (self.bone_id, self.recordType, frameIndex, k1.frameIndex, k2.frameIndex))
			
#				if(frameIndex < 0):
#					return self.values_header.p + self.values_header.dp * values[0].cp
#				elif(frameIndex > len(values)):
#					return self.values_header.p + self.values_header.dp * values[-1].cp
#				else:
#					for i in range(1, len(values)):
#						if(frameIndex == values[i-1].frameIndex):
#							return self.values_header.p + self.values_header.dp * values[i-1].cp
#						elif(frameIndex == values[i].frameIndex):
#							return self.values_header.p + self.values_header.dp * values[i].cp
#						elif(values[i-1].frameIndex < frameIndex < values[i].frameIndex):
#							p0 = self.values_header.p + self.values_header.dp * values[i-1].cp
#							m0 = self.values_header.m1 + self.values_header.dm1 * values[i-1].cm1
#							p1 = self.values_header.p + self.values_header.dp * values[i].cp
#							m1 = self.values_header.m0 + self.values_header.dm0 * values[i-1].cm0
#							t = 1.0 * (frameIndex - values[i-1].frameIndex)/(values[i].frameIndex - values[i-1].frameIndex)
#							val = (2*t*t*t - 3*t*t + 1)*p0 + (t*t*t - 2*t*t + t)*m0 + (-2*t*t*t + 3*t*t)*p1 + (t*t*t - t*t)*m1
#							return val
#						else:
#							print('[MOT-Error] Record frame outside bounds. boneNumber: %d, recordType: %d, frameIndex: %d, minBound: %d, maxBound: %d' % (self.bone_id, self.recordType, frameIndex, values[i-1].frameIndex, values[i].frameIndex))
			else:
				print('[MOT-Error] Unknown recordType %d at: %d' % self.recordType, self.offset)
			
			
class mot_values_header(object):
	def __init__(self, mot_file, recordType, valueCount):
		super(mot_values_header, self).__init__()
		self.offset = mot_file.tell()
		if recordType == 0:
			pass
		elif recordType == 1:
			self.values = []
			for i in range(valueCount):
				self.values.append(mot_value(mot_file, recordType))
		elif recordType == 2:
			self.p = to_float(mot_file.read(4)) #value
			self.dp = to_float(mot_file.read(4)) #value delta
			self.values = []
			for i in range(valueCount):
				self.values.append(mot_value(mot_file, recordType))
		elif recordType == 3:
			self.p = to_pghalf(mot_file.read(2)) #value
			self.dp = to_pghalf(mot_file.read(2)) #value delta
			self.values = []
			for i in range(valueCount):
				self.values.append(mot_value(mot_file, recordType))
		elif recordType == 4:
			self.values = []
			for i in range(valueCount):
				self.values.append(mot_value(mot_file, recordType))
		elif recordType == 5:
			self.p = to_float(mot_file.read(4)) #value
			self.dp = to_float(mot_file.read(4)) #value delta
			self.m0 = to_float(mot_file.read(4)) #incoming derivative
			self.dm0 = to_float(mot_file.read(4)) #incoming derivative delta
			self.m1 = to_float(mot_file.read(4)) #outgoing derivative
			self.dm1 = to_float(mot_file.read(4)) #outgoing derivative value delta
			self.values = []
			for i in range(valueCount):
				self.values.append(mot_value(mot_file, recordType))
		elif recordType == 6:
			self.p = to_pghalf(mot_file.read(2)) #value
			self.dp = to_pghalf(mot_file.read(2)) #value delta
			self.m0 = to_pghalf(mot_file.read(2)) #incoming derivative value
			self.dm0 = to_pghalf(mot_file.read(2)) #incoming derivative value delta
			self.m1 = to_pghalf(mot_file.read(2)) #outgoing derivative value
			self.dm1 = to_pghalf(mot_file.read(2)) #outgoing derivative value delta
			self.values = []
			for i in range(valueCount):
				self.values.append(mot_value(mot_file, recordType))
		elif recordType == 7:
			self.p = to_pghalf(mot_file.read(2)) #value
			self.dp = to_pghalf(mot_file.read(2)) #value delta
			self.m0 = to_pghalf(mot_file.read(2)) #incoming derivative value
			self.dm0 = to_pghalf(mot_file.read(2)) #incoming derivative value delta
			self.m1 = to_pghalf(mot_file.read(2)) #outgoing derivative value
			self.dm1 = to_pghalf(mot_file.read(2)) #outgoing derivative value delta
			self.values = []
			for i in range(valueCount):
				self.values.append(mot_value(mot_file, recordType))
		elif recordType == 8:
			self.p = to_pghalf(mot_file.read(2)) #value
			self.dp = to_pghalf(mot_file.read(2)) #value delta
			self.m0 = to_pghalf(mot_file.read(2)) #incoming derivative value
			self.dm0 = to_pghalf(mot_file.read(2)) #incoming derivative value delta
			self.m1 = to_pghalf(mot_file.read(2)) #outgoing derivative value
			self.dm1 = to_pghalf(mot_file.read(2)) #outgoing derivative value delta
			self.values = []
			for i in range(valueCount):
				self.values.append(mot_value(mot_file, recordType))
		else:
			print('[MOT-Error] Unknown recordType %d at: %d' % self.recordType, self.offset)
				
				
class mot_value(object):
	def __init__(self, mot_file, recordType):
		super(mot_value, self).__init__()
		if recordType == 0:
			pass
		elif recordType == 1:
			self.p = to_float(mot_file.read(4)) #value
		elif recordType == 2:
			self.cp = to_int(mot_file.read(2)) #value quantum
		elif recordType == 3:
			self.cp = to_int(mot_file.read(1)) #value quantum
		elif recordType == 4:
			self.frameIndex = to_int(mot_file.read(2)) #absolute frame index
			self.unknown1 = to_int(mot_file.read(2)) #dummy for alignment
			self.p = to_float(mot_file.read(4)) #value
			self.m0 = to_float(mot_file.read(4)) #incoming derivative
			self.m1 = to_float(mot_file.read(4)) #outgoing derivative
		elif recordType == 5:
			self.frameIndex = to_int(mot_file.read(2)) #absolute frame index
			self.cp = to_int(mot_file.read(2)) #value quantum
			self.cm0 = to_int(mot_file.read(2)) #incoming derivative quantum
			self.cm1 = to_int(mot_file.read(2)) #outgoing derivative quantum
		elif recordType == 6:
			self.frameIndex = to_int(mot_file.read(1)) #absolute frame index
			self.cp = to_int(mot_file.read(1)) #value quantum
			self.cm0 = to_int(mot_file.read(1)) #incoming derivative quantum
			self.cm1 = to_int(mot_file.read(1)) #outgoing derivative quantum
		elif recordType == 7:
			self.frameIndex = to_int(mot_file.read(1)) #relative frame index
			self.cp = to_int(mot_file.read(1)) #value quantum
			self.cm0 = to_int(mot_file.read(1)) #incoming derivative quantum
			self.cm1 = to_int(mot_file.read(1)) #outgoing derivative quantum
		elif recordType == 8:
			self.frameIndex = to_intB(mot_file.read(2)) #absolute frame index (big endian)
			self.cp = to_int(mot_file.read(1)) #value quantum
			self.cm0 = to_int(mot_file.read(1)) #incoming derivative quantum
			self.cm1 = to_int(mot_file.read(1)) #outgoing derivative quantum
		else:
			print('[MOT-Error] Unknown recordType %d at: %d' % self.recordType, super.offset)
		
		
class MOT(object):
	def __init__(self, mot_fp):
		super(MOT, self).__init__()
		mot_file = 0
		if os.path.exists(mot_fp):
			mot_file = open(mot_fp, 'rb')
		else:
			print("[MOT-Error] File does not exist at: %s" % mot_fp)
		
		self.magicNumber = mot_file.read(4)
		if self.magicNumber == b"mot\x00":
			self.unknown1 = to_int(mot_file.read(4))
			self.flags = to_int(mot_file.read(2))
			self.frameCount = to_int(mot_file.read(2))
			self.recordsOffset = to_int(mot_file.read(4))
			self.recordCount = to_int(mot_file.read(4))
			self.unknown2 = to_int(mot_file.read(4))
			self.motionName = to_string(mot_file.read(12))
		else:
			print("[MOT-Error] This file is not a MOT file.")
			
		self.records = []
		for i in range(self.recordCount):
			mot_file.seek(i*12 + self.recordsOffset)
			self.records.append(mot_record(mot_file))

		mot_file.close()


if __name__ == "__main__":
	useage = "\nUseage:\n    python mot.py mot_path\nEg:    python mot.py C:\\NierA\\pl0000_0619.mot"
	if len(sys.argv) < 1:
		print(useage)
		exit()
	if len(sys.argv) > 1:
		mot_fp = sys.argv[1]
	MOT(mot_fp)
	