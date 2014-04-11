import urllib, urllib2, socket, struct
from collections import deque
from threading import RLock, Thread

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Random import get_random_bytes
from hashlib import sha1

from cStringIO import StringIO

import packets
import datatypes

import binascii

import json

def javaHexDigest(digest):
	d = long(digest.hexdigest(), 16)
	if d >> 39 * 4 & 0x8:
		d = "-%x" % ((-d) & (2 ** (40 * 4) - 1))
	else:
		d = "%x" % d
	return d

class FailedLogin(Exception):
	pass

class Session(object):
	def login(self,username,password):
		url = 'https://authserver.mojang.com/authenticate'
		headers = {'Content-Type': 'application/json'}
		parameters = {
			"agent": {
				"name": "Minecraft",
				"version": 1
			},
			"username": username,
			"password": password
		}
		data = json.dumps(parameters)
		result = json.loads(urllib2.urlopen(urllib2.Request(url,headers=headers),data).read())
		try:
			self.username = result[u'selectedProfile'][u'name']
			self.access_token = result[u'accessToken']
			self.client_token = result[u'clientToken']
			self.uid = result[u'selectedProfile'][u'id']
		except ValueError:
			raise FailedLogin(result)

class EncryptWrapper(object):
	def __init__(self,stream,cipher):
		self.stream = stream
		self.cipher = cipher
	def read(self,length):
		return self.cipher.decrypt(self.stream.read(length))

class MineCraftConnection(object):
	transmit_cipher = None
	state = "disconnected"
	protocol_state = 'Handshaking'

	def __init__(self):
		self.lastmessages = deque(maxlen=10)
		self.transmitlock = RLock()
		for x in dir(packets):
			attr = getattr(packets,x)
			if hasattr(attr,'_packetdatatype'):
				cls = attr._packetdatatype
				self.registerHandler(cls,attr)

	def registerHandler(self,datatype,handler):
		#print("XRegistered handler for 0x%X" % datatype.id)
		self.handlers[datatype.id] = (datatype,handler)

	def start_session(self,session,host,port=25565):
		self.session = session
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((host,port))
		self.stream = self.socket.makefile("r")		
		self.send(packets.TransmitHandshake(4,host,port,2))
		self.protocol_state = 'Login'
		self.send(packets.TransmitLoginStart(session.username))

	def enableEncryption(self):
		self.transmit_cipher = AES.new(self.shared_key, AES.MODE_CFB, IV=self.shared_key)
		self.receive_cipher = AES.new(self.shared_key, AES.MODE_CFB, IV=self.shared_key)
		self.stream = EncryptWrapper(self.stream,self.receive_cipher)

	def send(self,packet):
		#print('sent %s' % packet)
		self.transmitlock.acquire()
		try:
			rawdata = packet.encode()
			#print(binascii.b2a_hex(rawdata))
			if self.transmit_cipher:
				self.socket.send(self.transmit_cipher.encrypt(buffer(rawdata)))
			else:
				self.socket.send(rawdata)
		finally:
			self.transmitlock.release()
	def recv(self):
		while True:
			try:
				length = datatypes.Varint.decode(self.stream)
				#print("recv size %s" % length)
				id = datatypes.Varint.decode(self.stream)
				#print("recv id %s" % id)
				if id > 0x7F:
					self.onDisconnect(packets.Disconnect("Id too long"))
					return
				data = self.stream.read(length - 1)
				#print(binascii.b2a_hex(data))
			except TypeError:
				self.onDisconnect(packets.Disconnect("Connection Lost"))
				raise			

			if (self.protocol_state,id) in packets.PacketRegistry.types:
				datatype = packets.PacketRegistry.types[(self.protocol_state,id)]
				#print(datatype)
				self.lastmessages.append(datatype.__name__)
				packet = datatype(raw=StringIO(data))
				handler = getattr(self,'on'+datatype.__name__,None)
				if handler:
					handler(packet)
			else:
				print("Skipping {0:#X} ({0})".format(id))
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
			'accessToken':self.session.access_token,
			'selectedProfile':self.session.uid,
			'serverId':javaHexDigest(hash),
		}
		url = 'https://sessionserver.mojang.com/session/minecraft/join'
		request = urllib2.Request(url,data=json.dumps(parameters),headers={'Content-Type': 'application/json'})
		result = urllib2.urlopen(request).read()
		self.RSACipher = PKCS1_v1_5.new(self.pubkey)
		encrypted_verify_token = self.RSACipher.encrypt(packet.verify_token)
		encrypted_shared_key = self.RSACipher.encrypt(self.shared_key)
		
		self.send(packets.TransmitEncryptionKeyResponse(encrypted_shared_key,encrypted_verify_token))
		self.enableEncryption()
	def onLoginSuccess(self,packet):
		self.send(packets.TransmitClientStatuses(0))
		self.state = "connected"
		self.protocol_state = 'Play'
	def onKeepAlive(self,packet):
		self.send(packets.TransmitKeepAlive(packet.keepalive_id))
