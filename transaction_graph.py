# used tranaction ids to get the CORRECT total ordering

import heapq, sys
import numpy as np
import db_tools

class HeapSet:
	def __init__(self, min_heap = True):
		self.heap = []
		self.elements = set([])
		self.min_heap = min_heap
	def add(self,tx):
		if tx not in self.elements:
			self.elements.add(tx)
			if self.min_heap:
				priority = tx.id
			else:
				priority = -tx.id
			heapq.heappush(self.heap, (priority, tx))
	def pop(self):
		priority, tx = heapq.heappop(self.heap)
		self.elements.remove(tx)
		if self.min_heap:
			return priority, tx
		else: 
			return -priority, tx
	def __len__(self):
		return len(self.heap)

class TransactionGraph:	
	def __init__(self):
		self.nodes = []
		self.edges = {}

	def addSourceAddress(self, address_string, index = 0):
		address = db_tools.Address(address_string)
		self.backwardInTime(address)
		self.forwardInTime(address)
	
	def backwardInTime(self, address):
		contaminated_txs = HeapSet(min_heap = False)
		
		funding_inputs = address.inputs
		total_contamination = 0
		for i,input in enumerate(funding_inputs):
			total_contamination += input.value # fix so you do not double count coins.
			input.rank = i
			self.addNode(input)
			contaminated_txs.add(input.transaction)

		while len(contaminated_txs) > 0 and len(self.nodes) < 50:
			tx_id, tx = contaminated_txs.pop()

			tx_contamination = np.zeros(len(funding_inputs))
			contaminated_outputs = []		
			contaminations = []	
			tx_rank = 0
			for output in tx.outputs:
				if output in funding_inputs:
					if output.contamination is None:
						output.contamination = np.zeros(len(funding_inputs))
					new_contamination = output.value - output.contamination.sum()
					output.contamination[funding_inputs.index(output)] = new_contamination
				if output.contamination is not None:
					tx_contamination += output.contamination
					contaminated_outputs.append(output)
					contaminations.append(output.contamination.sum())
					tx_rank = max(tx_rank,output.rank)

			contaminations = np.array(contaminations)
			
			try:
				input_value = tx.inputValue
			except KeyError: # tx is a coinbase transaction.
				continue

			for i,input in enumerate(tx.inputs):
				weight = input.value / input_value
				input.contamination = weight * tx_contamination
				input.rank = 10*tx_rank + i
				if input.value > total_contamination / 20:
					contaminated_txs.add(input.transaction)
					self.addNode(input)
					self.addEdges([input],contaminated_outputs,weight*contaminations)
		
	def forwardInTime(self, address):
		contaminated_txs = HeapSet(min_heap = True)
		total_contamination = 0

		funding_inputs = address.inputs

		for input in funding_inputs:
			total_contamination += input.value
			contaminated_txs.add(input.spend_transaction)

		while len(contaminated_txs) > 0 and len(self.nodes) < 100:
			tx_id, tx = contaminated_txs.pop()

			tx_contamination = np.zeros(len(funding_inputs))			
			contaminated_inputs = []
			contaminations = []
			tx_rank = 0
			for input in tx.inputs:
				if input.contamination is not None:
					tx_contamination += input.contamination
					contaminated_inputs.append(input)
					contaminations.append(input.contamination.sum())
					tx_rank = max(tx_rank,input.rank)
			
			contaminations = np.array(contaminations)
			input_value = tx.inputValue

			for i,output in enumerate(tx.outputs):
				weight = output.value / input_value
				if output.contamination is None:
					output.contamination = weight * tx_contamination
					output.rank = 10*tx_rank + i
				else:	
					untouched = output.contamination == 0
					output.contamination[untouched] = weight * tx_contamination[untouched]
				if output.contamination.sum() > total_contamination / 20:
					if output.spend_transaction != 'Unspent':
						contaminated_txs.add(output.spend_transaction)
					self.addNode(output)
					self.addEdges(contaminated_inputs,[output],weight*contaminations)

	def addNode(self,node):
		if node not in self.nodes:
			self.nodes.append(node)
	
	def addEdges(self,sources,sinks,weight):
		i = 0
		for source in sources:	
			for sink in sinks:
				if source in self.nodes and sink in self.nodes:
					self.edges[(source,sink)] = weight[i]
				i += 1
	
	def toDict(self):
		nodes = []
		for output in self.nodes:
			node = {}
			node['name'] = output.transaction
			node['color'] = colorFunction(output.contamination.sum() / output.value)
			node['btc_value'] = output.value / 1e8
			node['address'] = output.address
			node['rank'] = output.rank
			nodes.append(node)

		links = []
		for edge in self.edges:
			link = {}
			link['source'] = self.nodes.index(edge[0])
			link['target'] = self.nodes.index(edge[1])
			link['value'] = self.edges[edge] / 1e8
			links.append(link)
		
		return {'nodes': nodes, 'links': links}

def colorFunction(x):
	return '#' + colorScale(x) + colorScale(0) + colorScale(0) 

def colorScale(x):
	x = int(255 * x)
	result = chr(x).encode('hex')
	return result



if __name__ == '__main__':
	test_address = '15Fdz9eLuVJcq19vDeVPqXu1B6wuoyQ2kw'
	g = TransactionGraph()
	g.addSourceAddress(test_address)

	db_tools.instances = {}

	#pizza_address = '17SkEw2md5avVNyYgj6RiXuQKNwkXaxFyQ'
	#g = TransactionGraph()
	#g.addSourceAddress(pizza_address)

	#db_tools.instances = {}

	#mtgox_address = '1eHhgW6vquBYhwMPhQ668HPjxTtpvZGPC'
	#g = TransactionGraph()
	#g.addSourceAddress(mtgox_address)
	#g.connectEdges()