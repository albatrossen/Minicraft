import struct

class DataType():
	creation_counter = 0
	def __init__(self):
		self.creation_counter = DataType.creation_counter
		DataType.creation_counter += 1
	def encode(cls,value,buffer,index):
		raise NotImplementedError()
	def decode(cls,value,buffer,index):
		raise NotImplementedError()
		
class Double(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!d',buffer,index,value)
		return 8
	def decode(cls,stream):
		return struct.unpack('!d',stream.read(8))[0]
	def default(self):
		return 0

class Float(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!f',buffer,index,value)
		return 4
	def decode(cls,stream):
		return struct.unpack('!f',stream.read(4))[0]
	def default(self):
		return 0


class Long(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!q',buffer,index,value)
		return 8
	def decode(cls,stream):
		return struct.unpack('!q',stream.read(8))[0]
	def default(self):
		return 0

class Integer(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!i',buffer,index,value)
		return 4
	def decode(cls,stream):
		return struct.unpack('!i',stream.read(4))[0]
	def default(self):
		return 0
class IntegerArray(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!b',buffer,index,len(value))
		buffer[index+1:index+1+len(value)] = value
		return 1+ len(value)
	def decode(cls,stream):
		length = struct.unpack('!b',stream.read(1))[0]
		return [struct.unpack('!i',stream.read(4))[0] for x in range(length)]
	def default(self):
		return b''

class IntegerVector(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!iii',buffer,index,*value)
		return 4*3
	def decode(cls,stream):
		return struct.unpack('!iii',stream.read(4*3))
	def default(self):
		return 0
class ByteVectorArray(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!iii',buffer,index,*value)
		return 4*3
	def decode(cls,stream):
		length = struct.unpack('!i',stream.read(4))[0]
		return [struct.unpack('!bbb',stream.read(3)) for x in range(length)]
	def default(self):
		return 0
class Short(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!h',buffer,index,value)
		return 2
	def decode(cls,stream):
		return struct.unpack('!h',stream.read(2))[0]
	def default(self):
		return 0

class UShort(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!H',buffer,index,value)
		return 2
	def decode(cls,stream):
		return struct.unpack('!H',stream.read(2))[0]
	def default(self):
		return 0

class Byte(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!b',buffer,index,value)
		return 1
	def decode(cls,stream):
		return struct.unpack('!b',stream.read(1))[0]
	def default(self):
		return 0
class UByte(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!B',buffer,index,value)
		return 1
	def decode(cls,stream):
		return struct.unpack('!B',stream.read(1))[0]
	def default(self):
		return 0
class ObjectData(DataType):
	def decode(cls,stream):
		x = struct.unpack('!i',stream.read(4))[0]
		if x == 0:
			return (0,(0,0,0))
		else:
			return (x,struct.unpack('!hhh',stream.read(6)))
	def default(self):
		return 0
class Bool(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!b',buffer,index,int(value))
		return 1
	def decode(cls,stream):
		return bool(struct.unpack('!b',stream.read(1))[0])
	def default(self):
		return False

class Bytes(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!h',buffer,index,len(value))
		buffer[index+2:index+2+len(value)] = value
		return 2+ len(value)
	def decode(cls,stream):
		length = struct.unpack('!h',stream.read(2))[0]
		return stream.read(length)
	def default(self):
		return b''

class IBytes(DataType):
	def encode(cls,buffer,index,value):
		struct.pack_into('!i',buffer,index,len(value))
		buffer[index+4:index+4+len(value)] = value
		return 4+ len(value)
	def decode(cls,stream):
		length = struct.unpack('!i',stream.read(4))[0]
		return stream.read(length)
	def default(self):
		return b''

class Slot(DataType):
	def decode(self,stream):
		block_id = struct.unpack('!h',stream.read(2))[0]
		if block_id == -1:
			return (-1,0,0,"")
		item_count = struct.unpack('!b',stream.read(1))[0]
		item_damage = struct.unpack('!h',stream.read(2))[0]
		length = struct.unpack('!h',stream.read(2))[0]
		nbt_data = stream.read(length) if length != -1 else ''
		return (block_id,item_count,item_damage,nbt_data)
	def default(self):
		return b''

class Slots(Slot):
	def decode(self,stream):
		length = struct.unpack('!h',stream.read(2))[0]
		return [Slot.decode(self,stream) for x in range(length)]
	def default(self):
		return b''

class Varint(DataType):
	@classmethod
	def encode(cls,buffer,index,value):
		shifted_value = True
		bytes_written = 0
		while shifted_value:
			shifted_value = value >> 7
			buffer[index] = (chr((value & 0x7F) | (0x80 if shifted_value != 0 else 0x00)))
			value = shifted_value
			index += 1
			bytes_written += 1
		return bytes_written

	@classmethod
	def decode(cls,stream):
		value, shift, quantum = 0, 0, 0x80
		while (quantum & 0x80) == 0x80:
			quantum = ord(stream.read(1))
			value, shift = value + ((quantum & 0x7F) << shift), shift + 7
		return value

	def default(self):
		return 0

class String(DataType):
	def encode(cls,buffer,index,value):
		encoded = value.encode('utf-8')
		varint_size = Varint.encode(buffer,index,len(encoded))
		index += varint_size
		buffer[index:index+len(encoded)] = encoded
		return varint_size + len(encoded)
	def decode(cls,stream):
		length = Varint.decode(stream)
		encoded = stream.read(length)
		decoded = encoded.decode('utf-8')
		return decoded
	def default(self):
		return ''


class Metadata(Slot):
	types = {
		0:Byte(),
		1:Short(),
		2:Integer(),
		3:Float(),
		4:String(),
		5:Slot(),
		6:IntegerVector(),
	}
	def decode(self,stream):
		value = {}
		while True:
			item = struct.unpack('!B',stream.read(1))[0]
			if item == 0x7F:
				break
			index = item & 0x1F
			type = item >> 5
			value[index] = self.types[type].decode(stream)
		return value
	def default(self):
		return b''
