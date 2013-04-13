import urllib, urllib2, socket, struct
from collections import deque
from threading import RLock, Thread

from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Random import get_random_bytes
from hashlib import sha1

import packets

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
		url = 'https://login.minecraft.net'
		headers = {'Content-Type': 'application/x-www-form-urlencoded'}
		parameters = {
			'user': username,
			'password': password,
			'version': '13'
		}
		data = urllib.urlencode(parameters)
		result = urllib2.urlopen(url,data).read()
		try:
			timestamp,downloadticket,self.username,self.session_id,self.uid = result.split(":")
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
		self.send(packets.Handshake(60,self.session.username,host,port))

	def enableEncryption(self):
		self.transmit_cipher = AES.new(self.shared_key, AES.MODE_CFB, IV=self.shared_key)
		self.receive_cipher = AES.new(self.shared_key, AES.MODE_CFB, IV=self.shared_key)
		self.stream = EncryptWrapper(self.stream,self.receive_cipher)
	def send(self,packet):
		self.transmitlock.acquire()
		try:
			rawdata = packet.encode()
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
				self.onDisconnect(packets.Disconnect("Connection Lost"))
				return
			id = struct.unpack("!B",data)[0]
			if id in packets.PacketRegistry.types:
				datatype = packets.PacketRegistry.types[id]
				self.lastmessages.append(datatype.__name__)
				packet = datatype(raw=self.stream)
				handler = getattr(self,'on'+datatype.__name__,None)
				if handler:
					handler(packet)
			else:
				self.send(packets.Disconnect())
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
		
		self.send(packets.EncryptionKeyResponse(encrypted_shared_key,encrypted_verify_token))
	def onEncryptionKeyResponse(self,packet):
		self.enableEncryption()
		self.send(packets.ClientStatuses(0))
		self.state = "connected"
	def onKeepAlive(self,packet):
		self.send(packet)
