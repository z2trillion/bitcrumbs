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
		self.nodes = set([])
		self.edges = set([])

	def addSourceAddress(self, address_string, index = 0):
		address = db_tools.Address(address_string)
		self.backwardInTime(address)
		self.forwardInTime(address)
	
	def backwardInTime(self, address):
		contaminated_txs = HeapSet(min_heap = False)
		total_contamination = 0

		funding_inputs = address.inputs

		for input in funding_inputs:
			total_contamination += input.value
			contaminated_txs.add(input.transaction)

		while len(contaminated_txs) > 0:
			tx_id, tx = contaminated_txs.pop()

			tx_contamination = np.zeros(len(funding_inputs))			
			for output in tx.outputs:
				if output in funding_inputs:
					if output.contamination is None:
						output.contamination = np.zeros(len(funding_inputs))
					new_contamination = output.value - output.contamination.sum()
					output.contamination[funding_inputs.index(output)] = new_contamination
				if output.contamination is not None:
					tx_contamination += output.contamination
			
			try:
				input_value = tx.inputValue
			except KeyError:
				continue

			for input in tx.inputs:
				weight = input.value / input_value
				input.contamination = weight * tx_contamination
				if input.value > total_contamination / 200:
					contaminated_txs.add(input.transaction)
					self.addNode(input)
					self.addEdges(input,tx.outputs)
					print input
		
	def forwardInTime(self, address):
		contaminated_txs = HeapSet(min_heap = True)
		total_contamination = 0

		funding_inputs = address.inputs

		for input in funding_inputs:
			total_contamination += input.value
			contaminated_txs.add(input.transaction)

		while len(contaminated_txs) > 0:
			tx_id, tx = contaminated_txs.pop()

			tx_contamination = np.zeros(len(funding_inputs))			
			for input in tx.inputs:
				if input.contamination is not None:
					tx_contamination += input.contamination
			
			input_value = tx.inputValue

			for output in tx.outputs:
				weight = output.value / input_value
				if output.contamination is None:
					output.contamination = weight * tx_contamination
				else:	
					untouched = output.contamination == 0
					output.contamination[untouched] = weight * tx_contamination[untouched]
				if output.contamination.sum() > total_contamination / 200:
					if output.spend_transaction != 'Unspent':
						contaminated_txs.add(output.spend_transaction)
					print output

	def addNode(self,node):
		pass

	def addEdges(self,edge):
		pass

	def connectEdges(self):
		#print self.nodes
		for node in self.nodes:
			for sink, w0, w1 in node.sinks:
				if sink in self.nodes:
					self.edges.add((node,sink,w0,w1))
				#else:
				#	print 'not relevant!'
			#print node

	def toDict(self):
		graph = self.nodes
		txs = set([output.transaction for output in graph])
		txs |= set([output.spend_transaction for output in graph])
		txs = list(txs)

		weights = {}
		ordering = {}
		addresses = {}
		values = {}
		for i,output in enumerate(graph):
			taint = output.contamination / output.value
			weights[output.spend_transaction] = taint
			weights[output.transaction] = taint
			ordering[output.transaction] = i
			ordering[output.spend_transaction] = i
			addresses[output.transaction] = output.address
			addresses[output.spend_transaction] = output.address
			values[output.spend_transaction] = output.value
			values[output.transaction] = output.value

		node_index_map = {tx: i for i, tx in enumerate(txs)}
		nodes= []
		for tx in txs:
			node = {}
			node['name'] = tx
			node['color'] = color_function(weights[tx])
			node['xpos'] = ordering[tx]
			node['btc_value'] = values[tx] / 1e8
			node['address'] = addresses[tx]
			nodes.append(node)
		#nodes = [{'name':tx[:10],'color':weights[tx]} for tx in txs]

		edges = []
		for output in graph:
			source = node_index_map[output.transaction]
			sink = node_index_map[output.spend_transaction]
			edge = {'source': source, 'target': sink, 'value': output.contamination.sum()}
			edges.append(edge)
		
		return {'nodes': nodes, 'links': edges}

def color_function(t):
	r = t[0]
	try:
		g = t[1]
	except IndexError:
		g = 0
	try: 
		b = t[2]
	except IndexError:
		b = 0
	return '#' + colorScale(r) + colorScale(g) + colorScale(b) 

def colorScale(x):
	x = int(255 * np.sqrt(x))
	try:
		result = chr(x).encode('hex')
	except ValueError:
		print x
	return result



if __name__ == '__main__':
	pizza_address = '17SkEw2md5avVNyYgj6RiXuQKNwkXaxFyQ'
	g = TransactionGraph()
	g.addSourceAddress(pizza_address)

	db_tools.instances = {}

	mtgox_address = '1eHhgW6vquBYhwMPhQ668HPjxTtpvZGPC'
	g = TransactionGraph()
	g.addSourceAddress(mtgox_address)
	#g.connectEdges()