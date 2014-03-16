from minicraft.datatypes import *

import struct
import json

import binascii

def getMRO(cls):
	return (cls,) + sum(map(getMRO,cls.__bases__),())

class PacketRegistry(type):
	types = {}
	def __new__(cls, clsname, bases, attrs):
		newclass = super(cls, PacketRegistry).__new__(cls, clsname, bases, attrs)
		#print(cls, clsname, bases, attrs,newclass)  # here is your register function
		if 'id' in attrs:
			packet_id = attrs['id']
			packet_state = attrs['state'] if 'state' in attrs else 'Play'
			if (packet_state,packet_id) in PacketRegistry.types:
				print("WARNING CONFLICT")
				print("0x{:02X} -> {}".format(packet_id,PacketRegistry.types[(packet_state,packet_id)].__name__))
				print("0x{:02X} -> {}".format(packet_id,newclass.__name__))
			PacketRegistry.types[(packet_state,packet_id)] = newclass
		return newclass

class Packet(object):
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
			#print('Decoding %s' % name)
			value = datatype.decode(stream)
			setattr(self,name,value)
	def getFields(self):
		fields = [(name,dataType) for name,dataType in self.__class__.__dict__.items() if isinstance(dataType,DataType)]
		return sorted(fields,cmp=lambda (nameA,typeA),(nameB,typeB):cmp(typeA.creation_counter,typeB.creation_counter))
		
	def encode(self):
		output_buffer = bytearray(4096)
		index = Varint.encode(output_buffer,0,self.id)
		for name,datatype in self.getFields():
			index += datatype.encode(output_buffer,index,getattr(self,name))
			#print("|" + binascii.b2a_hex(output_buffer[:index]))
		packet_size = index
		index += Varint.encode(output_buffer,index,packet_size)
		return output_buffer[packet_size:index] + output_buffer[:packet_size]

class TransmitPacket(Packet):
	pass

class ReceivePacket(Packet):
	__metaclass__ = PacketRegistry

class TransmitHandshake(TransmitPacket):
	id = 0x00
	state = 'Handshaking'
	protocol_version = Varint()
	host = String()
	server_port = UShort()
	next_state = Varint()

class KeepAlive(ReceivePacket):
	id = 0x00
	keepalive_id = Integer()

class JoinGame(ReceivePacket):
	id = 0x01
	entity_id = Integer()
	gamemode = UByte()
	dimension = Byte()
	difficulty = UByte()
	max_players = UByte()
	level_type = String()

class ChatMessage(ReceivePacket):
	id = 0x02
	message = String()

class TimeUpdate(ReceivePacket):
	id = 0x03
	day = Long()
	time = Long()

class EntityEquipment(ReceivePacket):
	id = 0x04
	entity_id = Integer()
	slot = Short()
	item = Slot()

class SpawnPosition(ReceivePacket):
	id = 0x05
	x = Integer()
	y = Integer()
	z = Integer()

class UpdateHealth(ReceivePacket):
	id = 0x06
	health = Float()
	food = Short()
	food_saturation = Float()

class Respawn(ReceivePacket):
	id = 0x07
	dimension = Integer()
	difficulty = UByte()
	gamemode = UByte()
	leveltype = String()

class PlayerPositionAndLook(ReceivePacket):
	id = 0x08
	x = Double()
	y = Double()
	z = Double()
	yaw = Float()
	pitch = Float()
	on_ground = Bool()

class HeldItemChange(ReceivePacket):
	id = 0x09
	payload = Byte()

class UseBed(ReceivePacket):
	id = 0x0A
	entity_id = Integer()
	x = Integer()
	y = UByte()
	z = Integer()

class Animation(ReceivePacket):
	id = 0x0B
	entity_id = Integer()
	animation = UByte()

class SpawnNamedEntity(ReceivePacket):
	id = 0x0C
	entity_id = Varint()
	uuid = String()
	player_name = String()
	x = Integer()
	y = Integer()
	z = Integer()
	yaw = Byte()
	pitch = Byte()
	current_item = Short()
	metadata = Metadata()

class CollectItem(ReceivePacket):
	id = 0x0D
	collected_id = Integer()
	collector_id = Integer()

class SpawnObject(ReceivePacket):
	id = 0x0E
	entity_id = Varint()
	type = Byte()
	x = Integer()
	y = Integer()
	z = Integer()
	pitch = Byte()
	yaw = Byte()
	object_data = ObjectData()

class SpawnMob(ReceivePacket):
	id = 0x0F
	entity_id = Varint()
	type = UByte()
	x = Integer()
	y = Integer()
	z = Integer()
	pitch = Byte()
	head_pitch = Byte()
	yaw = Byte()
	velocity_x = Short()
	velocity_y = Short()
	velocity_z = Short()
	metadata = Metadata()

class SpawnPainting(ReceivePacket):
	id = 0x10
	entity_id = Varint()
	title = String()
	x = Integer()
	y = Integer()
	z = Integer()
	direction = Integer()

class SpawnExperienceOrb(ReceivePacket):
	id = 0x11
	entity_id = Varint()
	x = Integer()
	y = Integer()
	z = Integer()
	count = Short()

class EntityVelocity(ReceivePacket):
	id = 0x12
	entity_id = Varint()
	velocity_x = Short()
	velocity_y = Short()
	velocity_z = Short()

class DestroyEntity(ReceivePacket):
	id = 0x13
	entity_ids = IntegerArray()

class Entity(ReceivePacket):
	id = 0x14
	entity_id = Integer()

class EntityRelativeMove(ReceivePacket):
	id = 0x15
	entity_id = Integer()
	dx = Byte()
	dy = Byte()
	dz = Byte()

class EntityLook(ReceivePacket):
	id = 0x16
	entity_id = Integer()
	yaw = Byte()
	pitch = Byte()

class EntityLookAndRelativeMove(ReceivePacket):
	id = 0x17
	entity_id = Integer()
	dx = Byte()
	dy = Byte()
	dz = Byte()
	yaw = Byte()
	pitch = Byte()

class EntityTeleport(ReceivePacket):
	id = 0x18
	entity_id = Integer()
	x = Integer()
	y = Integer()
	z = Integer()
	yaw = Byte()
	pitch = Byte()

class EntityHeadLook(ReceivePacket):
	id = 0x19
	entity_id = Integer()
	yaw = Byte()

class EntityStatus(ReceivePacket):
	id = 0x1A
	entity_id = Integer()
	status = Byte()

class AttachEntity(ReceivePacket):
	id = 0x1B
	entity_id = Integer()
	vehicle_id = Integer()
	leash = Bool()

class EntityMetadata(ReceivePacket):
	id = 0x1C
	entity_id = Integer()
	metadata = Metadata()

class EntityEffect(ReceivePacket):
	id = 0x1D
	entity_id = Integer()
	effect_id = Byte()
	amplifier = Byte()
	durection = Short()

class RemoveEntityEffect(ReceivePacket):
	id = 0x1E
	entity_id = Integer()
	effect_id = Byte()

class SetExperience(ReceivePacket):
	id = 0x1F
	experience_bar = Float()
	level = Short()
	total_experience = Short()

class EntityProperties(ReceivePacket):
	id = 0x20
	entity_id = Integer()
	properties_count = Integer()
	key = String() #We need to read a bunch a bunch of these
	value = Double()
	list_length = Short()
	list_element = None
	def setFromRawData(self,stream):
		self.entity_id = self.entity_id.decode(stream)
		self.properties_count = self.properties_count.decode(stream)
		self.properties = {}
		for i in range(self.properties_count):
			key = self.key.decode(stream)
			value = self.value.decode(stream)
			self.properties[key] = value
			list_length = self.list_length.decode(stream)
			for i in range(list_length):
				uuid_msb, uuid_lsb, amount, operation  = struct.unpack('!qqdb',stream.read(25))

class ChunkData(ReceivePacket):
	id = 0x21
	x = Integer()
	y = Integer()
	ground_up = Bool()
	primary_bitmap = UShort()
	secondary_bitmap = UShort()
	data = IBytes()

class MultiBlockChange(ReceivePacket):
	id = 0x22
	x = Integer()
	z = Integer()
	record_count = Short()
	data = IBytes()

class BlockChange(ReceivePacket):
	id = 0x23
	x = Integer()
	y = UByte()
	z = Integer()
	block_type = Varint()
	block_metadata = Byte()

class BlockAction(ReceivePacket):
	id = 0x24
	x = Integer()
	y = Short()
	z = Integer()
	byte1 = UByte()
	byte2 = UByte()
	block_id = Varint()

class BlockBreakAnimation(ReceivePacket):
	id = 0x25
	entity_id = Varint()
	x = Integer()
	y = Integer()
	z = Integer()
	destro_stage = Byte()

class MapChunkBulk(ReceivePacket):
	id = 0x26
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

class Explosion(ReceivePacket):
	id = 0x27
	x = Float()
	y = Float()
	z = Float()
	radius = Float()
	records = ByteVectorArray()

class SoundOrParticleEffect(ReceivePacket):
	id = 0x28
	effect_id = Integer()
	x = Integer()
	y = Byte()
	z = Integer()
	data = Integer()
	disable_relative_volume = Bool()

class NamedSoundEffect(ReceivePacket):
	id = 0x29
	sound_name = String()
	x = Integer()
	y = Integer()
	z = Integer()
	volume = Float()
	pitch = Byte()

class Particle(ReceivePacket):
	id = 0x2A
	particle_name = String()
	x = Float()
	y = Float()
	z = Float()
	offset_x = Float()
	offset_x = Float()
	offset_x = Float()
	particle_data = Float()
	particle_number = Integer()

class ChangeGameState(ReceivePacket):
	id = 0x2B
	reason = UByte()
	gamemode = Float()

class SpawnGlobalEntity(ReceivePacket):
	id = 0x2C
	entity_id = Varint()
	type = Byte()
	x = Integer()
	y = Integer()
	z = Integer()

class OpenWindow(ReceivePacket):
	id = 0x2D
	window_id = UByte()
	inventory_type = UByte()
	window_title = String()
	number_of_slots = UByte()
	use_provided_window_title = Bool()
	entity_id = Integer()

class CloseWindow(ReceivePacket):
	id = 0x2E
	window_id = UByte()

class SetSlot(ReceivePacket):
	id = 0x2F
	window_id = Byte()
	slot = Short()
	slot_data = Slot()

class SetWindowItems(ReceivePacket):
	id = 0x30
	window_id = UByte()
	slots = Slots()

class UpdateWindowProperty(ReceivePacket):
	id = 0x31
	window_id = UByte()
	property = Short()
	value = Short()

class ConfirmTransaction(ReceivePacket):
	id = 0x32
	window_id = UByte()
	action_number = Short()
	accepted = Bool()

class UpdateSign(ReceivePacket):
	id = 0x33
	x = Integer()
	y = Short()
	z = Integer()
	text1 = String()
	text2 = String()
	text3 = String()
	text4 = String()

class Maps(ReceivePacket):
	id = 0x34
	item_damage = Varint()
	text = Bytes()

class UpdateTileEntity(ReceivePacket):
	id = 0x35
	x = Integer()
	y = Short()
	z = Integer()
	action = UByte()
	nbt_data = Bytes()

class SignEditorOpen():
	id = 0x36
	tile_entity_id = Byte()
	x = Integer()
	y = Integer()
	z = Integer()

class Statistic(ReceivePacket):
	id = 0x37
	count = Varint()
	entries = []
	statistic_name = String()
	amount = Varint()
	def setFromRawData(self,stream):
		self.count = self.count.decode(stream)
		entries = [(self.statistic_name.decode(stream),self.amount.decode(stream)) for x in range(self.count)]

class PlayerListItem(ReceivePacket):
	id = 0x38
	player_name = String()
	online = Bool()
	pin = Short()

class PlayerAbilities(ReceivePacket):
	id = 0x39
	flags = Byte()
	flying_speed = Float()
	walking_speed = Float()

class TabComplete(ReceivePacket):
	id = 0x3A
	count = Varint()
	completion = String()
	completions = []
	def setFromRawData(self,stream):
		self.count = self.count.decode(stream)
		self.completions = [self.completion.decode(stream) for x in range(x)]

class ScoreboardObjective(ReceivePacket):
	id = 0x3B
	objective_name = String()
	objective_value = String()
	create_remove = Byte()

class UpdateScore(ReceivePacket):
	id = 0x3C
	item_name = String()
	update_remove = Byte()
	score_name = String() #Conditional
	value = Integer() #Conditional
	def setFromRawData(self,stream):
		self.item_name = self.item_name.decode(stream)
		self.update_remove = self.update_remove.decode(stream)
		if self.update_remove != 1:
			self.score_name = self.score_name.decode(stream)
			self.value = self.value.decode(stream)
		else:
			self.score_name = None
			self.value = None

class DisplayScoreboard(ReceivePacket):
	id = 0x3D
	position = Byte()
	score_name = String()

class Teams(ReceivePacket):
	id = 0x3E
	team_name = String()
	mode = Byte()
	team_display_name = String()
	team_prefix = String()
	team_suffix = String()
	friendly_fire = Byte()
	player_count = Short()
	players = []
	def setFromRawData(self,stream):
		self.team_name = self.team_name.decode(stream)
		self.mode = self.mode.decode(stream)
		if self.mode == 0 or self.mode == 2:
			self.team_display_name = self.team_display_name.decode(stream)
			self.team_prefix = self.team_prefix.decode(stream)
			self.team_suffix = self.team_suffix.decode(stream)
			self.friendly_fire = self.friendly_fire.decode(stream)
		else:
			self.team_display_name = None
			self.team_prefix = None
			self.team_suffix = None
			self.friendly_fire = None
		if self.mode == 0 or self.mode == 3 or self.mode == 4:
			self.player_count = self.player_count.decode(stream)
			s=String()
			self.players = [s.decode(stream) for i in range(self.player_count)]

class PluginMessage(ReceivePacket):
	id = 0x3F
	channel = String()
	data = Bytes()

class Disconnect(ReceivePacket):
	id = 0x40
	reason = String()

class TransmitKeepAlive(TransmitPacket):
	id = 0x00
	keepalive_id = Integer()

class TransmitChatMessage(TransmitPacket):
	id = 0x01
	message = String()

class TransmitUseEntity(TransmitPacket):
	id = 0x02
	target = Integer()
	mouse_button = Byte()

class TransmitPlayer(TransmitPacket):
	id = 0x03
	on_ground = Bool()

class TransmitPlayerPosition(TransmitPacket):
	id = 0x04
	x = Double()
	head_y = Double()
	feet_y = Double()
	z = Double()
	on_ground = Bool()

class TransmitPlayerLook(TransmitPacket):
	id = 0x05
	yaw = Float()
	pitch = Float()
	on_ground = Bool()

class TransmitPlayerPositionAndLook(TransmitPacket):
	id = 0x06
	x = Double()
	head_y = Double()
	feet_y = Double()
	z = Double()
	yaw = Float()
	pitch = Float()
	on_ground = Bool()

class TransmitPlayerDigging(TransmitPacket):
	id = 0x07
	status = Byte()
	x = Integer()
	y = UByte()
	z = Integer()
	face = Byte()

class TransmitPlayerBlockPlacement(TransmitPacket):
	id = 0x08
	x = Integer()
	y = UByte()
	z = Integer()
	direction = Byte()
	held_item = Slot()
	cursor_x = Byte()
	cursor_y = Byte()
	cursor_z = Byte()


class TransmitHeldItemChange(TransmitPacket):
	id = 0x09
	slot = Short()

class TransmitAnimation(TransmitPacket):
	id = 0x0A
	entity_id = Integer()
	animation = Byte()

class TransmitEntityAction(TransmitPacket):
	id = 0x0B
	entity_id = Integer()
	action = Byte()
	jump_boost = Integer()

class TransmitSteerVehicle(TransmitPacket):
	id = 0x0C
	sideways = Float()
	forward = Float()
	jump = Bool()
	unmount = Bool()

class TransmitCloseWindow(TransmitPacket):
	id = 0x0D
	window_id = Byte()

class TransmitClickWindow(TransmitPacket):
	id = 0x0E
	window_id = Byte()
	slot = Short()
	mousebutton = Byte()
	action_number = Short()
	mode = Byte()
	clicked_item = Slot()

class TransmitConfirmTransaction(TransmitPacket):
	id = 0x0F
	window_id = Byte()
	action_number = Short()
	accepted = Bool()

class TransmitCreativeInventoryAction(TransmitPacket):
	id = 0x10
	slot = Short()
	clicked_item = Slot()

class TransmitEnchantItem(TransmitPacket):
	id = 0x11
	window_id = Byte()
	enchantment = Byte()

class TransmitUpdateSign(TransmitPacket):
	id = 0x12
	x = Integer()
	y = Short()
	z = Integer()
	text1 = String()
	text2 = String()
	text3 = String()
	text4 = String()

class TransmitPlayerAbilities(TransmitPacket):
	id = 0x13
	flags = Byte()
	flying_speed = Float()
	walking_speed = Float()

class TransmitTabComplete(TransmitPacket):
	id = 0x14
	message = String()

class TransmitClientSettings(TransmitPacket):
	id = 0x15
	locale = String()
	view_distance = Byte()
	chat_flags = Byte()
	chat_colours = Bool()
	difficulty = Byte()
	show_cape = Bool()

class TransmitClientStatuses(TransmitPacket):
	id = 0x16
	payload = Byte()

class TransmitPluginMessage(TransmitPacket):
	id = 0x17
	channel = String()
	data = Bytes()

class StatusResponse(ReceivePacket):
	id = 0x00
	state = 'Status'
	json_response = String()

class StatusPing(ReceivePacket):
	id = 0x01
	state = 'Status'
	time = Long()

class TransmitStatusRequest(TransmitPacket):
	id = 0x00
	state = 'Status'

class TransmitStatusPing(TransmitPacket):
	id = 0x01
	state = 'Status'
	time = Long()

class LoginDisconnect(ReceivePacket):
	id = 0x00
	state = 'Login'
	reason = String()

class EncryptionKeyRequest(ReceivePacket):
	id = 0x01
	state = 'Login'
	server_id = String()
	public_key = Bytes()
	verify_token = Bytes()

class LoginSuccess(ReceivePacket):
	id = 0x02
	state = 'Login'
	uuid = String()
	username = String()

class TransmitLoginStart(TransmitPacket):
	id = 0x00
	state = 'Login'
	name = String()

class TransmitEncryptionKeyResponse(TransmitPacket):
	id = 0x01
	state = 'Login'
	shared_secret = Bytes()
	verify_token_response = Bytes()

