class BitReader: 
	def readInt(self,n_bytes):
		return int(self.read(n_bytes)[::-1].encode('hex'),16)
	def readHex(self,n_bytes):
		return self.read(n_bytes).encode('hex')
	def readVarInt(self):
		first_byte	=	ord(self.read(1))
		if first_byte<=0xfc:
			return first_byte
		elif first_byte==0xfd:
			return self.readInt(2)
		elif first_byte==0xfe:
			return self.readInt(4)
		elif first_byte==0xff:
			return self.readInt(8)
