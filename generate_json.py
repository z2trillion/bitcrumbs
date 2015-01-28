import sys, heapq
import numpy as np
import pymysql as mdb
import json
from graph_to_json import graphToDict

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

#try:
address = sys.argv[1]
#except IndexError:
#	address = '1eHhgW6vquBYhwMPhQ668HPjxTtpvZGPC'#'17SkEw2md5avVNyYgj6RiXuQKNwkXaxFyQ'
	#address = '17SkEw2md5avVNyYgj6RiXuQKNwkXaxFyQ'

tainteds = getSourceOutputs(address)

total_amount = 0
for tainted in tainteds.elements.values():
	tainteds[tainted].amount = tainted.value
	total_amount += tainted.value
unspent_outputs = []

graph = []

while len(tainteds) > 0:
	output = tainteds.pop()
	if output.amount < total_amount / 100 or output.amount / output.value < .1:
		continue
	elif output.spendHash == NULL_HASH:
		unspent_outputs.append(output)
	else:
		entry = [output.transactionHash]
		entry.append(output.spendHash)
		entry.append(output.amount)
		entry.append(output.amount/output.value)
		graph.append(entry)
		txOutputValue = float(getTxOutputValue(output.spendHash))
		for linked_output in getLinkedOutputs(output):
			tainteds.add(linked_output)
		for linked_output in getLinkedOutputs(output):
			weight = linked_output.value / txOutputValue
			increment = weight * tainteds[output].amount
			tainteds[linked_output].amount += increment

json_output = open('/Users/mason/Desktop/app/static/data/output.json','w')
json.dump(graphToDict(graph),json_output)


