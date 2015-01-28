import hashlib

b58 = ('123456789' +
		'ABCDEFGHJKLMNPQRSTUVWXYZ' +
		'abcdefghijkmnopqrstuvwxyz')
def toBase58(n):
	result = ''
	while n > 0:
		result = b58[n%58] + result
		n /= 58
	return result

def toBase256(n):
	result = ''
	n = int(n,16)
	while n > 0:
		result = chr(n%256) + result
		n /= 256
	return result

def OP_HASH256(s):
	x=hashlib.sha256(s)
	y=hashlib.sha256(x.digest())
	return y.hexdigest()

def OP_HASH160(s):
	x = hashlib.sha256(s)
	y = hashlib.new('ripemd160')
	y.update(x.digest())
	return y.hexdigest()


def toBase58Check(version,payload):
	extended = chr(version) + toBase256(payload)
	checksum = OP_HASH256(extended)[:8]
	extended16 = str(version)+payload+checksum
	n_leading_zeros = 1+next((i for i,x in enumerate(payload) if '0'!=x),0)/2
	result = n_leading_zeros*'1' + toBase58(int(str(version)+payload+checksum,16))
	return result

class OutputTransaction:
	def __init__(self,value,script):
		self.value = value
		if script[:6] == '76a914':
			self.template = 'public key hash'
			self.address = toBase58Check(0,script[6:46])
		elif script[:2] == '41':
			self.template = 'public key'
			public_key_hash = OP_HASH160(toBase256(script[2:2+65*2]))
			self.address = toBase58Check(0,public_key_hash)
		else:
			self.template = 'other'
			self.address = None

if __name__ == '__main__':
	import numpy as np
	test_addresses = np.loadtxt('head_balances.txt',skiprows=3,usecols=(1,2),dtype='str')
	for hash160,b58check in test_addresses:
		assert b58check == toBase58Check(0,hash160)
