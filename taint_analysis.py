import sys, heapq
import numpy as np
import pymysql as mdb

NULL_HASH = 64*'0'

class PriorityDict():
	def __init__(self):
		self.heap = [] # for keys of self.elements
		self.elements = {}
	def add(self,element):
		priority = element.blockNumber
		key = (element.transactionHash,element.outputIndex)
		if key not in self.elements:
			heapq.heappush(self.heap,(priority,key))
			self.elements[key] = element
	def pop(self):
		priority,key = heapq.heappop(self.heap)
		return self.elements[key]
	def __len__(self):
		return len(self.heap)
	def __getitem__(self,output):
		return self.elements[(output.transactionHash,output.outputIndex)]

class Output:
	def __init__(self,parameters,taint=0):
		self.amount = 0.0
		self.taint = 0.0
		self.blockNumber = parameters[0]
		self.outputIndex = parameters[1]
		self.spendHash = parameters[2]
		self.transactionHash = parameters[3]
		self.value = parameters[4]
	def __hash__(self):
		return hash((self.outputIndex,self.transactionHash))
	def __eq__(self,other):
		return hash(self) == hash(other)

con = mdb.connect('localhost','root','','bitcoin')
cur = con.cursor()

def getTxInputValue(transaction_hash):
	command = 'SELECT SUM(value) FROM outputs WHERE spendHash = "%s"'
	command = command % (transaction_hash)
	cur.execute(command)
	return cur.fetchone()[0]

def getTxOutputValue(transaction_hash):
	command = 'SELECT SUM(value) FROM outputs WHERE transactionHash = "%s"'
	command = command % (transaction_hash)
	cur.execute(command)
	return cur.fetchone()[0]

def getSourceOutputs(source_address):
	command = 'SELECT blockNumber, outputIndex, spendHash, transactionHash, value ' 
	command += 'FROM outputs WHERE address = "%s"' %source_address
	cur.execute(command)
	sources = PriorityDict()
	for entry in cur.fetchall():
		output = Output(entry)
		output.amount = output.value
		output.taint = 1.0
		sources.add(output)
	return sources

def getLinkedOutputs(output):
	command = 'SELECT blockNumber,outputIndex,spendHash,transactionHash,value '
	command += 'FROM outputs WHERE transactionHash = "%s"'
	command = command % output.spendHash
	cur.execute(command)
	return [Output(entry) for entry in cur.fetchall()]

tainteds = getSourceOutputs(sys.argv[1])
popped = 0
for tainted in tainteds.elements.values():
	tainteds[tainted].amount = tainted.value
unspent_outputs = []
while len(tainteds) > 0:
	output = tainteds.pop()
	if output.amount < 1e12 or output.amount / output.value < .4:
		print output.transactionHash,output.spendHash,
		print '%e' %output.amount, 
		print '%.3f' %(output.amount / output.value)
		continue
	elif output.spendHash == NULL_HASH:
		unspent_outputs.append(output)
	else:
		print output.transactionHash,output.spendHash,
		print '%e' %output.amount, 
		print '%.3f' %(output.amount / output.value)
		txOutputValue = float(getTxOutputValue(output.spendHash))
		for linked_output in getLinkedOutputs(output):
			tainteds.add(linked_output)
		for linked_output in getLinkedOutputs(output):
			weight = linked_output.value / txOutputValue
			increment = weight * tainteds[output].amount
			tainteds[linked_output].amount += increment
	popped += 1
	if popped % 1000 == 0:
		print len(tainteds), popped


