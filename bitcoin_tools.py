from bit_reader import BitReader
from script_parser import OutputTransaction
from data_file import DataFile
from hashlib import sha256

#need to refactor to the avoid the char->hex->string absurdities

def OP_SHA256(s):
	x=sha256(s)
	y=sha256(x.digest())
	return y.hexdigest()

class BlockChain:
	def __init__(self,data_directory='/Users/mason/Library/Application Support/Bitcoin/blocks/'):
		self.data_file	=	DataFile(data_directory)
	def __iter__(self):
		return self
	def next(self):
		assert self.data_file.readHex(4)=='f9beb4d9'
		block_length=self.data_file.readInt(4)
		return Block(self.data_file.read(block_length))

class Block(BitReader):
	def __init__(self,byte_data):
		self.current				=	byte_data
		self.current_index	=	0
		self.header					=	self.read(80)
		self.hash						=	OP_SHA256(self.header)
		self.previous_hash	=	self.header[4:36].encode('hex')
		self.n_tx				=	self.readVarInt()
		self.tx_counter	=	0
	def __iter__(self):
		return self
	def next(self):
		if self.tx_counter < self.n_tx:
			self.tx_counter += 1
			return Transaction(self)
		else:
			raise StopIteration
	def read(self,n_bytes):
		read_in	=	self.current[self.current_index:self.current_index+n_bytes]
		self.current_index += n_bytes
		return read_in

class Transaction:
	def __init__(self,block):
		start_index			=	block.current_index
		version_number	=	block.readInt(4)
		n_inputs				=	block.readVarInt()
		self.inputs			=	[TransactionInput(block) for i in range(n_inputs)]
		self.n_outputs	=	block.readVarInt()
		self.outputs		=	[TransactionOutput(block) for i in range(self.n_outputs)]
		lock_time				=	block.readInt(4)
		end_index				=	block.current_index
		self.hash				=	OP_SHA256(block.current[start_index:end_index])

class TransactionInput:
	def __init__(self,block):
		self.tx_hash					=	block.readHex(32)
		self.tx_index					=	block.readInt(4)
		self.script_length		=	block.readVarInt()
		self.script						=	block.read(self.script_length)
		self.sequence_number	=	block.readInt(4)

class TransactionOutput:
	def __init__(self,block):
		self.value					=	block.readInt(8)
		self.script_length	=	block.readVarInt()
		raw_script = block.read(self.script_length).encode('hex')
		self.address = OutputTransaction(self.value,raw_script).address

if __name__=='__main__':
	bc	=	BlockChain()
	block_counter	=	0
	for b in bc:
		if block_counter==123456:
			print block_counter,b.n_tx
			for i,tx in enumerate(b):
				#print 'tx.hash =',tx.hash
				#for input_address in tx.inputs:
				#	print input_address.tx_hash
				for output in tx.outputs:
					print i,output.address
			break
		block_counter+=1
