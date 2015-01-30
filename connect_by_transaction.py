import heapq, sys
import numpy as np
from database_tools import Address, Transaction

NULL_HASH = 64*'0'

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

class DirectedGraph:
	def __init__(self):
		self.nodes = set([])
		self.edges = []

class TransactionGraph(DirectedGraph):	
	def __init__(self, source_address):
		DirectedGraph.__init__(self)
		self.backwardinTime(source_address)
		self.forwardInTime(source_address)

	def backwardinTime(self,source_address):
		source_address = Address(source_address)
		contaminated_inputs = PrioritySet(min_heap = False)
		total_contamination = 0
		for input in source_address.incomingTxs():
			input.contamination = float(input.value)
			total_contamination += input.contamination
			contaminated_inputs.add(input)
		while len(contaminated_inputs) > 0 and len(self.nodes) < 100:
			height, input = contaminated_inputs.pop()
			if input.contamination < total_contamination / 50 or input.taint() < 0.1:
				continue
			else:
				self.addNode(input)
			total_output_value = float(input.transaction.outputValue())
			for previous_input in input.previousInputs():
				previous_input = contaminated_inputs.add(previous_input)
				weight = float(previous_input.value) / total_output_value
				additional_contamination = weight * input.contamination
				previous_input.contamination += additional_contamination

	def forwardInTime(self, source_address):
		source_address = Address(source_address)
		contaminated_outputs = PrioritySet()
		total_contamination = 0

		for tx in source_address.outgoingTxs():
			for output in tx.outputs():
				output.contamination = float(output.value)
				total_contamination += output.contamination
				contaminated_outputs.add(output)
		while len(contaminated_outputs) > 0 and len(self.nodes) < 200:
			height, output = contaminated_outputs.pop()
			if output.contamination < total_contamination / 50 or output.taint < 0.1:
				continue
			else:
				self.addNode(output)
			for next_output in output.nextOutputs():
				next_output = contaminated_outputs.add(next_output)
				weight = float(next_output.value) / float(output.spend_transaction.inputValue())
				additional_contamination = weight * output.contamination
				next_output.contamination += additional_contamination	
	def addNode(self,node):
		self.nodes.add(node)
	def toDict(self):
		graph = self.nodes
		txs = set([output.transaction for output in graph])
		txs |= set([output.spend_transaction for output in graph])
		txs = list(txs)

		weights = {}
		ordering = {}
		for i,output in enumerate(graph):
			taint = output.contamination / output.value
			weights[output.transaction] = taint
			weights[output.spend_transaction] = taint
			ordering[output.transaction] = i
			ordering[output.spend_transaction] = i

		node_index_map = {tx: i for i, tx in enumerate(txs)}
		nodes= []
		for tx in txs:
			node = {}
			node['name'] = tx[:10]
			node['color'] = weights[tx]
			node['xpos'] = ordering[tx]
			nodes.append(node)
		#nodes = [{'name':tx[:10],'color':weights[tx]} for tx in txs]

		edges = []
		for output in graph:
			source = node_index_map[output.transaction]
			sink = node_index_map[output.spend_transaction]
			edge = {'source': source, 'target': sink, 'value': output.contamination}
			edges.append(edge)
		
		return {'nodes': nodes, 'links': edges}


if __name__ == '__main__':
	pizza_address = Address('17SkEw2md5avVNyYgj6RiXuQKNwkXaxFyQ')
	TransactionGraph(pizza_address)

	mtgox_address = Address('1eHhgW6vquBYhwMPhQ668HPjxTtpvZGPC')
	json = graphToDict(transactionGraph(mtgox_address))
	print json