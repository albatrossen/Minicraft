
def hexdump(bytes, length=16):
	result = []
	for i in xrange(0, len(bytes), length):
		s = bytes[i:i+length]
		hexa = b' '.join(["%0*X" % (2, byte)  for byte in s])
		text = b''.join([chr(byte) if 0x20 <= byte < 0x7F else b'.'  for byte in s])
		result.append( b"%04X   %-*s   %s" % (i, length*(2 + 1), hexa, text) )
	return b'\n'.join(result)


import socket, urllib, urllib2, binascii

import struct

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Random import get_random_bytes
from hashlib import sha1
from collections import deque
from threading import RLock, Thread

# This function courtesy of barneygale
def javaHexDigest(digest):
    d = long(digest.hexdigest(), 16)
    if d >> 39 * 4 & 0x8:
        d = "-%x" % ((-d) & (2 ** (40 * 4) - 1))
    else:
        d = "%x" % d
    return d

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

class String(DataType):
	def encode(cls,buffer,index,value):
		encoded = value.encode('utf-16-be')
		struct.pack_into('!h',buffer,index,len(value))
		buffer[index+2:index+2+len(encoded)] = encoded
		return 2+ len(encoded)
	def decode(cls,stream):
		length = struct.unpack('!h',stream.read(2))[0]*2
		encoded = stream.read(length)
		decoded = encoded.decode('utf-16-be')
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

def getMRO(cls):
	return (cls,) + sum(map(getMRO,cls.__bases__),())

class PacketRegistry(type):
	types = {}
	def __new__(cls, clsname, bases, attrs):
		newclass = super(cls, PacketRegistry).__new__(cls, clsname, bases, attrs)
		#print(cls, clsname, bases, attrs,newclass)  # here is your register function
		if 'id' in attrs:
			pid = attrs['id']
			if pid in PacketRegistry.types:
				print("WARNING OVERRIDE")
			PacketRegistry.types[pid] = newclass
			print("0x{:02X} -> {}".format(pid,newclass.__name__))
		return newclass

class Packet(object):
	__metaclass__ = PacketRegistry
	def __init__(self,*args,**kwargs):
		if 'raw' in kwargs:
			self.setFromRawData(stream=kwargs['raw'])
		else:
			fields = self.getFields()
			for (name,datatype),value in zip(fields,args):
				setattr(self,name,value)
			for name,datatype in fields[len(args):]:
				setattr(self,name,datatype.default())
	def setFromRawData(self,stream):
		fields = self.getFields()
		for name,datatype in fields:
			value = datatype.decode(stream)
			setattr(self,name,value)
	def getFields(self):
		fields = [(name,dataType) for name,dataType in self.__class__.__dict__.items() if isinstance(dataType,DataType)]
		return sorted(fields,cmp=lambda (nameA,typeA),(nameB,typeB):cmp(typeA.creation_counter,typeB.creation_counter))
		
	def encode(self):
		output_buffer = bytearray(4096)
		index = 1
		struct.pack_into('!B',output_buffer,0,self.id)
		
		for name,datatype in self.getFields():
			index += datatype.encode(output_buffer,index,getattr(self,name))
		return output_buffer[:index]

class KeepAlive(Packet):
	id = 0x00
	keepalive_id = Integer()

class LoginRequest(Packet):
	id = 0x01
	entity_id = Integer()
	level_type = String()
	gamemode = Byte()
	dimension = Byte()
	difficulty = Byte()
	not_used = Byte()
	max_players = Byte()

class Handshake(Packet):
	id = 0x02
	protocol_version = Byte()
	username = String()
	server_host = String()
	server_port = Integer()


class ChatMessage(Packet):
	id = 0x03
	message = String()

class TimeUpdate(Packet):
	id = 0x04
	day = Long()
	time = Long()
class EntityEquipment(Packet):
	id = 0x05
	entity_id = Integer()
	slot = Short()
	item = Slot()
class SpawnPosition(Packet):
	id = 0x06
	x = Integer()
	y = Integer()
	z = Integer()
class UseEntity(Packet):
	id = 0x07
	user = Integer()
	target = Integer()
	mouse_button = Bool()
class UpdateHealth(Packet):
	id = 0x08
	health = Short()
	food = Short()
	food_saturation = Float()
class Respawn(Packet):
	id = 0x09
	dimension = Integer()
	difficulty = Byte()
	gamemode = Byte()
	worldheight = Short()
	leveltype = String()

class Player(Packet):
	id = 0x0A
	on_ground = Bool()

class PlayerPosition(Packet):
	id = 0x0B
	x = Double()
	y = Double()
	stance = Double()
	z = Double()
	on_ground = Bool()

class PlayerLook(Packet):
	id = 0x0C
	yaw = Float()
	pitch = Float()
	on_ground = Bool()

class PlayerPositionAndLook(Packet):
	id = 0x0D
	x = Double()
	y = Double()
	stance = Double()
	z = Double()
	yaw = Float()
	pitch = Float()
	on_ground = Bool()

class PlayerDigging(Packet):
	id = 0x0E
	status = Byte()
	x = Integer()
	y = Integer()
	z = Integer()
	face = Byte()

class PlayerBlockPlacement(Packet):
	id = 0x0F
	status = Byte()
	x = Integer()
	y = UByte()
	z = Integer()
	direction = Byte()
	held_item = Slot()
	cursor_x = Byte()
	cursor_y = Byte()
	cursor_z = Byte()
class HeldItemChange(Packet):
	id = 0x10
	payload = Short()
class UseBed(Packet):
	id = 0x11
	entity_id = Integer()
	unknown = Byte()
	x = Integer()
	y = Byte()
	z = Integer()

class Animation(Packet):
	id = 0x12
	entity_id = Integer()
	animation = Byte()

class EntityAction(Packet):
	id = 0x13
	entity_id = Integer()
	action = Byte()
class SpawnNamedEntity(Packet):
	id = 0x14
	entity_id = Integer()
	player_name = String()
	x = Integer()
	y = Integer()
	z = Integer()
	yaw = Byte()
	pitch = Byte()
	current_item = Short()
	metadata = Metadata()
class CollectItem(Packet):
	id = 0x16
	collected_id = Integer()
	collector_id = Integer()
class SpawnObjectVehicle(Packet):
	id = 0x17
	entity_id = Integer()
	type = Byte()
	x = Integer()
	y = Integer()
	z = Integer()
	yaw = Byte()
	pitch = Byte()
	object_data = ObjectData()
class SpawnMob(Packet):
	id = 0x18
	entity_id = Integer()
	type = Byte()
	x = Integer()
	y = Integer()
	z = Integer()
	yaw = Byte()
	pitch = Byte()
	head_Yaw = Byte()
	velocity_x = Short()
	velocity_y = Short()
	velocity_z = Short()
	metadata = Metadata()
class SpawnPainting(Packet):
	id = 0x19
	entity_id = Integer()
	title = String()
	x = Integer()
	y = Integer()
	z = Integer()
	direction = Integer()

class SpawnExperienceOrb(Packet):
	id = 0x1A
	entity_id = Integer()
	x = Integer()
	y = Integer()
	z = Integer()
	count = Short()
class EntityVelocity(Packet):
	id = 0x1C
	entity_id = Integer()
	velocity_x = Short()
	velocity_y = Short()
	velocity_z = Short()
class DestroyEntity(Packet):
	id = 0x1D
	entity_ids = IntegerArray()

class Entity(Packet):
	id = 0x1E
	entity_id = Integer()
class EntityRelativeMove(Packet):
	id = 0x1F
	entity_id = Integer()
	dx = Byte()
	dy = Byte()
	dz = Byte()
class EntityLook(Packet):
	id = 0x20
	entity_id = Integer()
	yaw = Byte()
	pitch = Byte()
class EntityLookAndRelativeMove(Packet):
	id = 0x21
	entity_id = Integer()
	dx = Byte()
	dy = Byte()
	dz = Byte()
	yaw = Byte()
	pitch = Byte()
class EntityTeleport(Packet):
	id = 0x22
	entity_id = Integer()
	x = Integer()
	y = Integer()
	z = Integer()
	yaw = Byte()
	pitch = Byte()
class EntityHeadLook(Packet):
	id = 0x23
	entity_id = Integer()
	yaw = Byte()
class EntityStatus(Packet):
	id = 0x26
	entity_id = Integer()
	status = Byte()
class AttachEntity(Packet):
	id = 0x27
	entity_id = Integer()
	vehicle_id = Integer()
class EntityMetadata(Packet):
	id = 0x28
	entity_id = Integer()
	metadata = Metadata()
class EntityEffect(Packet):
	id = 0x29
	entity_id = Integer()
	effect_id = Byte()
	amplifier = Byte()
	durection = Short()
class RemoveEntityEffect(Packet):
	id = 0x2A
	entity_id = Integer()
	effect_id = Byte()
class SetExperience(Packet):
	id = 0x2B
	experience_bar = Float()
	level = Short()
	total_experience = Short()
class ChunkData(Packet):
	id = 0x33
	x = Integer()
	y = Integer()
	ground_up = Bool()
	primary_bitmap = UShort()
	secondary_bitmap = UShort()
	data = IBytes()
class MultiBlockChange(Packet):
	id = 0x34
	x = Integer()
	z = Integer()
	record_count = Short()
	data = IBytes()
class BlockChange(Packet):
	id = 0x35
	x = Integer()
	y = Byte()
	z = Integer()
	block_type = Short()
	block_metadata = Byte()
class BlockAction(Packet):
	id = 0x36
	x = Integer()
	y = Short()
	z = Integer()
	byte1 = Byte()
	byte2 = Byte()
	block_id = Short()
class BlockAction(Packet):
	id = 0x37
	entity_id = Integer()
	x = Integer()
	y = Integer()
	z = Integer()
	destro_stage = Byte()

class MapChunkBulk(Packet):
	id = 0x38
	chunk_column_count = 0
	sky_light_sent = False
	data = b""
	meta = []
	def setFromRawData(self,stream):
		self.chunk_column_count, data_length, sky_light_sent_byte  = struct.unpack('!hib',stream.read(7))
		self.sky_light_sent = bool(sky_light_sent_byte)
		self.data = stream.read(data_length)
		self.meta = [self.readChunk(stream) for x in range(self.chunk_column_count)]
	def readChunk(self,stream):
		return struct.unpack('!iiHH',stream.read(12))
class Explosion(Packet):
	id = 0x3C
	x = Double()
	y = Double()
	z = Double()
	radius = Float()
	records = ByteVectorArray()
class SoundOrParticleEffect(Packet):
	id = 0x3D
	effect_id = Integer()
	x = Integer()
	y = Byte()
	z = Integer()
	data = Integer()
	disable_relative_volume = Bool()
class NamedSoundEffect(Packet):
	id = 0x3E
	sound_name = String()
	x = Integer()
	y = Integer()
	z = Integer()
	volume = Float()
	pitch = Byte()
class ChangeGameState(Packet):
	id = 0x46
	reason = Byte()
	gamemode = Byte()
class SpawnGlobalEntity(Packet):
	id = 0x47
	entity_id = Integer()
	type = Byte()
	x = Integer()
	y = Integer()
	z = Integer()
class OpenWindow(Packet):
	id = 0x64
	window_id = Byte()
	inventory_type = Byte()
	window_title = String()
	number_of_slots = Byte()
class OpenWindow(Packet):
	id = 0x65
	window_id = Byte()
class ClickWindow(Packet):
	id = 0x66
	window_id = Byte()
	slot = Short()
	mousebutton = Byte()
	action_number = Short()
	shift = Bool()
	clicked_item = Slot()
class SetSlot(Packet):
	id = 0x67
	window_id = Byte()
	slot = Short()
	slot_data = Slot()

class SetWindowItems(Packet):
	id = 0x68
	payload = Byte()
	slots = Slots()
class UpdateWindowProperty(Packet):
	id = 0x69
	window_id = Byte()
	property = Short()
	value = Short()
class ConfirmTransaction(Packet):
	id = 0x6A
	window_id = Byte()
	action_number = Short()
	accepted = Bool()

class ConfirmTransaction(Packet):
	id = 0x6B
	slot = Short()
	clicked_item = Slot()

class EnchantItem(Packet):
	id = 0x6C
	window_id = Byte()
	enchantment = Byte()

class UpdateSign(Packet):
	id = 0x82
	x = Integer()
	y = Short()
	z = Integer()
	text1 = String()
	text2 = String()
	text3 = String()
	text4 = String()

class ItemData(Packet):
	id = 0x83
	item_type = Short()
	item_id = Short()
	text = Bytes()
class UpdateTileEntity(Packet):
	id = 0x84
	x = Integer()
	y = Short()
	z = Integer()
	action = Byte()
	nbt_data = Bytes()
class IncrementStatistic(Packet):
	id = 0xC8
	statistic_id = Integer()
	amount = Byte()

class PlayerListItem(Packet):
	id = 0xC9
	player_name = String()
	online = Bool()
	pin = Short()
class PlayerAbilities(Packet):
	id = 0xCA
	flags = Byte()
	flying_speed = Byte()
	walking_speed = Byte()
class TabComplete(Packet):
	id = 0xCB
	text = String()
class ClientSettings(Packet):
	id = 0xCC
	locale = String()
	view_distance = Byte()
	chat_flags = Byte()
	difficulty = Byte()
	show_cape = Bool()
class ClientStatuses(Packet):
	id = 0xCD
	payload = Byte()
class PluginMessage(Packet):
	id = 0xFA
	channel = String()
	data = Bytes()

class EncryptionKeyResponse(Packet):
	id = 0xFC
	shared_secret = Bytes()
	verify_token_response = Bytes()
class EncryptionKeyRequest(Packet):
	id = 0xFD
	server_id = String()
	public_key = Bytes()
	verify_token = Bytes()

class Disconnect(Packet):
	id = 0xFF
	window_id = String()

def handler(cls):
	def wrapper(fun):
		fun._packetdatatype = cls
		return fun
	return wrapper



import re

class Session():
	def __init__(self,username,password):
		self.username = username
		self.login(username,password)
	def login(self,username,password):
		url = 'https://login.minecraft.net'
		headers = {'Content-Type': 'application/x-www-form-urlencoded'}
		parameters = {
			'user': username,
			'password': password,
			'version': '13'
		}
		data = urllib.urlencode(parameters)
		result = urllib2.urlopen(url,data).read()
		timestamp,downloadticket,username,self.session_id,uid = result.split(":")

class EncryptWrapper():
	def __init__(self,stream,cipher):
		self.stream = stream
		self.cipher = cipher
	def read(self,length):
		return self.cipher.decrypt(self.stream.read(length))


class MineCraftConnection():
	transmit_cipher = None
	control_matcher = re.compile("\xa7.")
	def __init__(self,session,host='elera.dk',port=25565):
		self.session = session
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((host,port))
		self.handlers = {}
		self.stream = self.socket.makefile("r")
		self.lastmessages = deque(maxlen=10)
		self.transmitlock = RLock()
		
		for x in dir(self):
			attr = getattr(self,x)
			if hasattr(attr,'_packetdatatype'):
				cls = attr._packetdatatype
				self.registerHandler(cls,attr)
		
		self.send(Handshake(51,self.session.username,host,port))
		p = Thread(target=self.recv)
		p.start()
		while True:
			try:
				r = raw_input()
			except KeyboardInterrupt:
				self.send(Disconnect())
				r = None
				break
			if r:
				self.send(ChatMessage(r[:100]))
		p.join()

	def registerHandler(self,datatype,handler):
		#print("XRegistered handler for 0x%X" % datatype.id)
		self.handlers[datatype.id] = (datatype,handler)

	def enableEncryption(self):
		print("Enabling encryption")
		self.transmit_cipher = AES.new(self.shared_key, AES.MODE_CFB, IV=self.shared_key)
		self.receive_cipher = AES.new(self.shared_key, AES.MODE_CFB, IV=self.shared_key)
		self.stream = EncryptWrapper(self.stream,self.receive_cipher)
	def send(self,packet):
		self.transmitlock.acquire()
		try:
			rawdata = packet.encode()
			#~ print(">%r" % rawdata)
			if self.transmit_cipher:
				self.socket.send(self.transmit_cipher.encrypt(buffer(rawdata)))
			else:
				self.socket.send(rawdata)
		finally:
			self.transmitlock.release()
	def recv(self):
		data = True
		while data:
			data = self.stream.read(1)
			if not data:
				return
			id = struct.unpack("!B",data)[0]
			if id in PacketRegistry.types:
				datatype = PacketRegistry.types[id]
				#print(datatype.__name__)
				self.lastmessages.append(datatype.__name__)
				packet = datatype(raw=self.stream)
				handler = getattr(self,'on'+datatype.__name__,None)
				if handler:
					handler(packet)
			else:
				self.send(Disconnect())
				print("LastTypes {0}".format(', '.join(self.lastmessages)))
				print("Missing handler for {0:#X} ({0})".format(id))
				return
			if id == 0xFF:
				return
	def onUnhandled(self,packet):
		print("<" + packet.__class__.__name__)
	def onEncryptionKeyRequest(self,packet):
		self.pubkey = RSA.importKey(packet.public_key)
		self.shared_key = get_random_bytes(16)
		hash = sha1()
		hash.update(packet.server_id)
		hash.update(self.shared_key)
		hash.update(packet.public_key)
		parameters = {
			'user':self.session.username,
			'sessionId':self.session.session_id,
			'serverId':javaHexDigest(hash),
		}
		url = 'http://session.minecraft.net/game/joinserver.jsp?' + urllib.urlencode(parameters)
		result = urllib2.urlopen(url).read()
		if result != "OK":
			print("Unexpected Result: " + result)
		self.RSACipher = PKCS1_v1_5.new(self.pubkey)
		encrypted_verify_token = self.RSACipher.encrypt(packet.verify_token)
		encrypted_shared_key = self.RSACipher.encrypt(self.shared_key)
		
		self.send(EncryptionKeyResponse(encrypted_shared_key,encrypted_verify_token))
	def onEncryptionKeyResponse(self,packet):
		self.enableEncryption()
		self.send(ClientStatuses(0))
	def onKeepAlive(self,packet):
		self.send(packet)
	def onChatMessage(self,packet):
		print(self.control_matcher.sub('',packet.message))

import getpass
MineCraftConnection(Session(username='Faua',password=getpass.getpass("Password:")),host="damnation.eu")