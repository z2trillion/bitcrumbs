import pymysql as mdb
import numpy as np

con = mdb.connect('localhost','root','','bitcoin')
cur = con.cursor()

class Address(str):

	def incomingTxs(self):
		command = 'SELECT DISTINCT(transactionHash) '
		command += 'FROM outputs '
		command += 'WHERE address = "%s" ' % self
		cur.execute(command)
		results = cur.fetchall()

		return [Transaction(row) for row in cur.fetchall()]

	def outgoingTxs(self):
		command = 'SELECT DISTINCT(spendHash) '
		command += 'FROM outputs '
		command += 'WHERE address = "%s" ' % self
		cur.execute(command)
		return [Transaction(row[0]) for row in cur.fetchall()]	

	def countInputs(self):
		command = 'SELECT COUNT(*) '
		command += 'FROM outputs '
		command += 'WHERE address = "%s" ' % self
		cur.execute(command)
		return int(cur.fetchone()[0])

	def inputs(self):
		command = 'SELECT * '
		command += 'FROM outputs '
		command += 'WHERE address = "%s" ' % self
		cur.execute(command)
		return [Coins(row) for row in cur.fetchall()]

	def outputs(self):
		command = 'SELECT b.* '
		command += 'FROM outputs a, outputs b '
		command += 'WHERE a.address = "%s" ' % self
		command += 'AND a.spendHash = b.transactionHash'
		cur.execute(command)
		return [Coins(row) for row in cur.fetchall()]
	
	def value(self,block_number):
		command = 'SELECT SUM(value) '
		command += 'FROM outputs WHERE address = "%s" ' % self
		command += 'AND blockNumber <= %i' % block_number
		cur.execute(command)
		try:
			total_in = int(cur.fetchone()[0])
		except TypeError:
			total_in = 0
		command = 'SELECT SUM(b.value) '
		command += 'FROM outputs a, outputs b '
		command += 'WHERE a.address = "%s" ' % self
		command += 'AND a.spendHash = b.transactionHash '
		command += 'AND b.blockNumber <= %i' %block_number
		cur.execute(command)
		try:
			total_out = int(cur.fetchone()[0])
		except TypeError:
			total_out = 0
		return total_in - total_out

class Transaction(str):

	def inputs(self):
		command = 'SELECT * FROM outputs '
		command += 'WHERE spendHash = "%s" ' %self 
		cur.execute(command)
		return [Coins(row) for row in cur.fetchall()]

	def height(self):
		command = 'SELECT blockNumber FROM outputs '
		command += 'WHERE transactionHash = "%s" LIMIT 1' %self
		cur.execute(command)
		return cur.fetchone()[0]

	def inputValue(self):
		command = 'SELECT SUM(value) FROM outputs WHERE spendHash = "%s"'
		command = command % self
		cur.execute(command)
		try:
			return float(cur.fetchone()[0])
		except TypeError:
			return 0.0

	def outputs(self):
		command = 'SELECT * FROM outputs '
		command += 'WHERE transactionHash = "%s" ' %self 
		cur.execute(command)
		return [Coins(row) for row in cur.fetchall()]

	def __hash__(self):
		return hash('%s' %self)

NULL_HASH = 64*'0'

def multiton(cls):
	instances = {}
	def getInstance(row):
		key = tuple(row[:2])
		if key not in instances:
			instances[key] = cls(row)
		return instances[key]
	return getInstance

@multiton # on transction and output index
class Coins:
	def __init__(self, row):
		self.transaction = Transaction(row[0])
		self.output_index = row[1]
		self.value = float(row[2])
		self.height = int(row[3])
		self.spend_transaction = Transaction(row[4])
		self.address = Address(row[5])

		self.sinks = set([])
		self.is_source = False
		self.contamination = 0

	def nextOutputs(self):
		command = 'SELECT * FROM outputs '
		command += 'WHERE transactionHash = "%s" ' % self.spend_transaction 
		cur.execute(command)
		return [Coins(row) for row in cur.fetchall()]
	
	def previousInputs(self):
		command = 'SELECT * FROM outputs '
		command += 'WHERE spendHash = "%s" ' % self.transaction
		cur.execute(command)
		return [Coins(row) for row in cur.fetchall()]
	
	def __str__(self):
		string = 'height: %i ' %self.height
		string += 'address: %s ' %self.address
		string += 'value: %e ' %self.value
		string += 'contamination: %e ' %self.contamination
		#assert self.contamination[0] <= self.value
		#string += 'taint: %e ' %(self.contamination.max() / self.value)
		#string += 'backward_taint: %e ' %(self.backward_contamination[0] / self.value)
		#string += 'taint: %.2f' % (self.contamination / self.value)
		return string

	def forward_taint(self, index):
		contamination = self.forward_contamination[index]
		return float(contamination) / self.value 

	def backward_taint(self, index):
		contamination = self.backward_contamination[index]
		return float(contamination) / self.value 
	
	def notSpent(self):
		return self.spend_transaction == NULL_HASH
	
	def addSink(self, coins, flow):
		self.sinks.add((coins,) + tuple(flow))

if __name__ == '__main__':
	pizza_address = Address('17SkEw2md5avVNyYgj6RiXuQKNwkXaxFyQ')
	assert pizza_address.value(57042) == 0
	assert pizza_address.value(57043) == int(1e12)
	assert pizza_address.value(57044) == 0
	assert len(pizza_address.getInputs()) == 1
	assert len(pizza_address.getOutputs()) == 2
	assert len(pizza_address.nextTxs(57041)) == 1
	assert len(pizza_address.nextTxs(57042)) == 1
	assert len(pizza_address.nextTxs(57043)) == 1
	assert len(pizza_address.nextTxs(57044)) == 1
	assert len(pizza_address.nextTxs(57045)) == 0
	inout_address = Address('1PrwYMffhu1XJyVXs6Ba67NidGZVjbGHCq')
	assert len(inout_address.nextTxs(64683)) == 1


