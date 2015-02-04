import heapq, sys
import numpy as np
from database_tools import Address, Transaction, Coins

class PrioritySet():
	def __init__(self, min_heap = True):
		self.heap = [] # heap of keys to elements
		self.elements = {}
		self.min_heap = min_heap
	def add(self,element):
		try:
			return self.elements[element]
		except KeyError:
			if self.min_heap:
				priority = element.height
			else:
				priority = -element.height
			heapq.heappush(self.heap,(priority,element))
			self.elements[element] = element
			return element
	def pop(self):
		priority,element = heapq.heappop(self.heap)
		del self.elements[element]
		return priority,element
	def __len__(self):
		return len(self.heap)
	def __getitem__(self,output):
		return self.elements[output]

class WeightedDAG:
	def __init__(self):
		self.nodes = set([])
		self.edges = set([])
	def addNode(self,node):
		self.nodes.add(node)
	def addEdge(self,edge):
		self.edges.add(edge)

class Edge:
	def __init__(self, source, sink, flows):
		self.source = source
		self.sink = sink
		self.flows = flows

class Node:
	def __init__(self,coins,coinbase=False,unspent=False):
		self.block_height = coins.height
		self.address = coins.address
		self.coinbase = coinbase
		self.unspent = unspent
		self.contamination = coins.contamination

class TransactionGraph(WeightedDAG):	
	def __init__(self):
		WeightedDAG.__init__(self)

	def addSourceAddress(self, address_string, index=0):
		address = Address(address_string)
		self.backwardInTime(address, index)
		self.forwardInTime(address, index)

	def backwardInTime(self, source_address, index):
		contaminated_inputs = PrioritySet(min_heap = False)
		total_contamination = 0

		for input in source_address.outgoingTxs():
			input.contamination[i] = float(input.value)
			except AttributeError:
				input.contamination = np.zeros(len(source_addresses))
				input.contamination[i] = float(input.value)
			total_contamination[i] += input.contamination[i]
			contaminated_inputs.add(input)
		
		while len(contaminated_inputs) > 0 and len(self.nodes) < 100:
			height, input = contaminated_inputs.pop()
			
			if (np.less(input.contamination, total_contamination / 70)).prod() == 1:
				continue
			elif (input.taint() < 0.01).prod() == 1:
				continue
			else:
				self.addNode(input)
			
			total_output_value = float(input.transaction.outputValue())
			for i, previous_input in enumerate(input.previousInputs()):
				previous_input = contaminated_inputs.add(previous_input)
				weight = float(previous_input.value) / total_output_value
				additional_contamination = weight * input.contamination
				try:
					previous_input.contamination += additional_contamination
				except AttributeError:
					previous_input.contamination = np.copy(additional_contamination)

	def forwardInTime(self, source_addresses):
		contaminated_outputs = PrioritySet()
		total_contamination = np.zeros(len(source_addresses))
		for i, address in enumerate(source_addresses):
			for tx in address.outgoingTxs():
				for output in tx.outputs():
					output = contaminated_outputs.add(output)
					try:
						output.contamination[i] = float(output.value)
					except AttributeError:
						output.contamination = np.zeros(len(source_addresses))
						output.contamination[i] = float(output.value)
					total_contamination[i] += output.contamination[i]
		while len(contaminated_outputs) > 0 and len(self.nodes) < 200:
			height, output = contaminated_outputs.pop()

			if np.less(output.contamination, total_contamination / 70).prod() > 0:
				continue
			elif (output.taint() < 0.01).prod() > 0:
				continue
			else:
				self.addNode(output)

			for next_output in output.nextOutputs():
				next_output = contaminated_outputs.add(next_output)
				weight = float(next_output.value) / float(output.spend_transaction.inputValue())
				additional_contamination = weight * output.contamination
				try:
					next_output.contamination += additional_contamination	
				except AttributeError:
					next_output.contamination = np.copy(additional_contamination)

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
	pizza_address = Address('17SkEw2md5avVNyYgj6RiXuQKNwkXaxFyQ')
	print TransactionGraph([pizza_address]).toDict()

	mtgox_address = Address('1eHhgW6vquBYhwMPhQ668HPjxTtpvZGPC')
	print TransactionGraph([pizza_address,mtgox_address]).toDict()