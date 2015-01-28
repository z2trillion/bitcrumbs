from bit_reader import BitReader
class DataFile(BitReader): 
	def __init__(self,directory):
		self.directory = directory
		self.file_counter = 0
		self.openNext(0) 
		self.current_index = self.current.find('\xf9\xbe\xb4\xd9')

	def openNext(self,n_bytes_left):
		next_file_name	=	self.directory+'blk%05d.dat'%self.file_counter
		with open(next_file_name,'rb') as next_file:
			self.current = next_file.read()
		self.current_index = 0
		self.file_counter += 1
		return self.read(n_bytes_left)
	
	def read(self,n_bytes):
		read_in	=	self.current[self.current_index:self.current_index+n_bytes]
		if len(read_in) < n_bytes:
			read_in += self.openNext(n_bytes - len(read_in))
		else:
			self.current_index += n_bytes
		return read_in
