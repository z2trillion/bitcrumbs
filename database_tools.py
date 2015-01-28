import pymysql as mdb

con = mdb.connect('localhost','root','','bitcoin')
cur = con.cursor()

class Address(str):
	def outgoingTxs(self):
		command = 'SELECT head.transactionHash FROM outputs tail, outputs head '
		command += 'WHERE tail.address = "%s" ' % self
		command += 'AND tail.spendHash = head.transactionHash'
		cur.execute(command)
		return [Transaction(tx[0]) for tx in cur.fetchall()]
	def getInputs(self, height):
		command = 'SELECT * FROM outputs '
		command += 'WHERE address = "%s"' % self
		command += 'AND blockNumber = %i' % height
		cur.execute(command)
		inputs = [Output(entry) for entry in cur.fetchall()]
		return inputs
	def getOutputs(self, height):
		command = 'SELECT b.* '
		command += 'FROM outputs a, outputs b '
		command += 'WHERE a.address = "%s" ' % self
		command += 'AND a.spendHash = b.transactionHash '
		command += 'AND b.blockNumber = %i' % block_number
		cur.execute(command)
		return [Output(entry) for entry in cur.fetchall()]
	def nextTxs(self,block_number):
		command = 'SELECT MIN(b.blockNumber) FROM outputs a, outputs b '
		command += 'WHERE a.address = "%s" ' % self
		command += 'AND a.spendHash = b.transactionHash '
		command += 'AND b.blockNumber >= %i' % block_number
		cur.execute(command)
		try:
			next_block = int(cur.fetchone()[0])
		except TypeError:
			next_block = 1e9 # this is not a long term solution.
		command = 'SELECT DISTINCT b.transactionHash, b.blockNumber FROM outputs a, outputs b '
		command += 'WHERE a.address = "%s" ' % self
		command += 'AND a.spendHash = b.transactionHash '
		command += 'AND b.blockNumber = %i' % next_block
		cur.execute(command)
		return [(Transaction(row[0]),row[1]) for row in cur.fetchall()] 
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
	def getTxs(self,block_number = -1):
		command = 'SELECT transactionHash FROM outputs '
		command += 'WHERE address = "%s"' % self
		cur.execute()
		return [Transaction(tx_string) for tx_string in cur.fetchall()]
class Transaction(str):
	def inputAddresses(self):
		command = 'SELECT address, value FROM outputs WHERE spendHash = "%s"'
		command = command % self
		cur.execute(command)
		return [(Address(row[0]), row[1]) for row in cur.fetchall()]
	def inputValue(self):
		command = 'SELECT SUM(value) FROM outputs WHERE spendHash = "%s"'
		command = command % self
		cur.execute(command)
		try:
			return cur.fetchone()[0]
		except TypeError:
			return 0
	def outputAddresses(self):
		command = 'SELECT address, value FROM outputs WHERE transactionHash = "%s"'
		command = command % self
		cur.execute(command)
		return [(Address(row[0]), row[1]) for row in cur.fetchall()]
	def outputValue(self):
		command = 'SELECT SUM(value) FROM outputs WHERE transactionHash = "%s"'
		command = command % self
		cur.execute(command)
		try:
			return int(cur.fetchone()[0])
		except TypeError:
			return 0
	def outputs(self):
		command = 'SELECT * FROM outputs WHERE transactionHash = "%s"'
		command = command % self
		cur.execute(command)
		return [Output(entry) for entry in cur.fetchall()]
	def height(self):
		command = 'SELECT blockNumber FROM outputs '
		command += 'WHERE transactionHash = "%s" LIMIT 1' % self
		cur.execute(command)
		return int(cur.fetchone()[0])
class Output:
	def __init__(self,row):
		self.transaction = Transaction(row[0])
		self.output_index = row[1]
		self.value = row[2]
		self.height = int(row[3])
		self.spend_transaction = Transaction(row[4])
		self.address = Address(row[5])
		self.contamination = 0.0
	def __hash__(self):
		return hash((self.output_index,self.transaction))
	def __eq__(self,other):
		return hash(self) == hash(other)
	def getSpendTransactions(self):
		command = 'SELECT * FROM outputs '
		command += 'WHERE transactionHash = "%s" ' % self.spend_transaction 
		cur.execute(command)
		return [Output(row) for row in cur.fetchall()]
	def __str__(self):
		string = 'height: %s ' % self.height
		string += 'contamination: %e ' % self.contamination
		string += 'taint: %.2f' % (self.contamination / self.value)
		return string


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


