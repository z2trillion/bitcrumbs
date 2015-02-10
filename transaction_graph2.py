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

cutoff = 50

class TransactionGraph:	
	def __init__(self):
		self.nodes = []
		self.edges = {}

	def clear(self):
		db_tools.instances = {}

	def addSourceAddress(self, address_string, index = 0):
		address = db_tools.Address(address_string)
		self.backwardInTime(address)
		self.forwardInTime(address)
	
	def backwardInTime(self, address):
		contaminated_outputs = HeapSet(min_heap = False)
		
		self.funding_inputs = address.inputs
		self.funding_ids = np.array([input.id for input in self.funding_inputs])

		total_contamination = 0
		for i,input in enumerate(self.funding_inputs):
			total_contamination += input.value # fix so you do not double count coins.
			input.rank = i
			input.is_source = 2
			contaminated_outputs.add(input)

		while len(contaminated_outputs) > 0 and len(self.nodes) < 50:
			output_id, output = contaminated_outputs.pop()

			if output in self.funding_inputs:
				if output.contamination is None:
					output.contamination = np.zeros(len(self.funding_inputs))
				assert output.contamination[self.funding_inputs.index(output)] == 0 
				additional_contamination = output.value - output.contamination.sum()
				output.contamination[self.funding_inputs.index(output)] = additional_contamination
				assert np.abs(output.contamination.sum() - output.value) < .1, (output.contamination.sum(), output.value) 

			if output.contamination.sum() < total_contamination / cutoff:
				continue
			else:
				self.addNode(output)

			for i,input in enumerate(output.transaction.inputs):
				weight = input.value / output.transaction.inputValue
				if input.contamination is None:
					input.contamination = weight * output.contamination
				else:
					input.contamination += weight * output.contamination
				assert input.contamination.sum() <= input.value + .1
				input.rank = 10*output.rank + i
				contaminated_outputs.add(input)
				self.addEdge(input, output, weight * output.contamination.sum())
		
	def forwardInTime(self, address):
		contaminated_inputs = HeapSet(min_heap = True)
		total_contamination = 0

		for input in self.funding_inputs:
			total_contamination += input.value
			contaminated_inputs.add(input)

		while len(contaminated_inputs) > 0 and len(self.nodes) < 100:
			input_id, input = contaminated_inputs.pop()

			if input.contamination.sum() < total_contamination / cutoff:
				continue
			elif input.spend_transaction == 'Unspent':
				continue	
			else:
				self.addNode(input)

			for i, output in enumerate(input.spend_transaction.outputs):
				weight = output.value / input.spend_transaction.inputValue
				if output.contamination is None:
					output.contamination = weight * input.contamination
				else:
					mask = input_id > self.funding_ids
					output.contamination[mask] += weight * input.contamination[mask]
				assert output.contamination.sum() <= output.value + .1
				output.rank = 10*input.rank + i
				contaminated_inputs.add(output)
				self.addEdge(input, output, weight * input.contamination.sum())

	def addNode(self,node):
		if node not in self.nodes:
			self.nodes.append(node)
	
	def addEdge(self,source,sink,weight):
		self.edges[(source,sink)] = weight

	def removeChains(self):
		# count number of inputs and outputs to a node.
		# if 1 and 1, then do
		pass
	
	def toDict(self):
		nodes = []
		for output in self.nodes:
			node = {}
			node['name'] = output.transaction
			node['color'] = colorFunction(output.contamination.sum() / output.value)
			node['btc_value'] = output.value / 1e8
			node['address'] = output.address
			node['rank'] = output.rank
			node['is_source'] = output.is_source
			node['contamination'] = output.contamination.sum() / 1e8
			node['time'] = output.height
			nodes.append(node)

		links = []
		for source, target in self.edges:
			link = {}
			if source not in self.nodes or target not in self.nodes:
				continue
			link['source'] = self.nodes.index(source)
			link['target'] = self.nodes.index(target)
			link['value'] = self.edges[(source, target)] / 1e8
			link['time'] = target.height
			links.append(link)
		
		return {'nodes': nodes, 'links': links}

def colorFunction(x):
	return '#' + colorScale(x) + colorScale(0) + colorScale(0) 

def colorScale(x):
	x = int(255 * np.sqrt(x))
	result = chr(x).encode('hex')
	return result



if __name__ == '__main__':
	test_address = '18c11RMANxg7aq6eqJ4MPe6dqvcwZtAAwk'
	g = TransactionGraph()
	g.addSourceAddress(test_address)
	print g.toDict()

	db_tools.instances = {}

	#pizza_address = '17SkEw2md5avVNyYgj6RiXuQKNwkXaxFyQ'
	#g = TransactionGraph()
	#g.addSourceAddress(pizza_address)

	#db_tools.instances = {}

	#mtgox_address = '1eHhgW6vquBYhwMPhQ668HPjxTtpvZGPC'
	#g = TransactionGraph()
	#g.addSourceAddress(mtgox_address)
	#g.connectEdges()