import heapq, sys
import numpy as np
from database_tools import Address, Output, Transaction

NULL_HASH = 64*'0'

class PrioritySet():
	def __init__(self):
		self.heap = [] # heap of keys to elements
		self.elements = {}
	def add(self,element):
		if element not in self.elements:
			priority = element.height
			heapq.heappush(self.heap,(priority,element))
			self.elements[element] = element
	def pop(self):
		priority,element = heapq.heappop(self.heap)
		del self.elements[element]
		return priority,element
	def __len__(self):
		return len(self.heap)
	def __getitem__(self,output):
		return self.elements[output]

def transactionGraph(source_address):
	source_address = Address(source_address)
	transaction_graph = []
	contaminated_outputs = PrioritySet()
	total_contamination = 0
	for tx in source_address.outgoingTxs():
		for output in tx.outputs():
			output.contamination = float(output.value)
			total_contamination += output.contamination
			contaminated_outputs.add(output)
	while len(contaminated_outputs) > 0:
		height, oldest_output = contaminated_outputs.pop()
		taint = oldest_output.contamination / oldest_output.value
		if oldest_output.spend_transaction == str(None):
			continue
		elif oldest_output.contamination < total_contamination / 50 or taint < 0.1:
			continue
		else:
			transaction_graph.append(oldest_output)
		for connected_output in oldest_output.spend_transaction.outputs():
			contaminated_outputs.add(connected_output)
			weight = float(connected_output.value) / float(oldest_output.spend_transaction.inputValue())
			additional_contamination = weight * oldest_output.contamination
			contaminated_outputs[connected_output].contamination += additional_contamination
	return transaction_graph

def graphToDict(graph):
	nodes = set([output.transaction for output in graph])
	nodes |= set([output.spend_transaction for output in graph])
	nodes = list(nodes)

	weights = {}
	for output in graph:
		taint = output.contamination / output.value
		weights[output.transaction] = taint
		weights[output.spend_transaction] = taint

	node_index_map = {transaction: i for i, transaction in enumerate(nodes)}
	nodes = [{'name':name[:10],'color':weights[name]} for name in nodes]

	edges = []
	for output in graph:
		source = node_index_map[output.transaction]
		sink = node_index_map[output.spend_transaction]
		edge = {'source': source, 'target': sink, 'value': output.contamination}
		edges.append(edge)
	
	return {'nodes': nodes, 'links': edges}

def graphToDict2(graph):
	txs = set([output.transaction for output in graph])
	txs |= set([output.spend_transaction for output in graph])
	txs = list(txs)

	weights = {}
	for output in graph:
		taint = output.contamination / output.value
		weights[output.transaction] = taint
		weights[output.spend_transaction] = taint

	node_index_map = {tx: i for i, tx in enumerate(txs)}
	nodes= []
	for tx in txs:
		node = {}
		node['name'] = tx[:10]
		node['color'] = weights[tx]
		if tx.height() is not None:
			node['xpos'] = tx.height()
		else:
			node['xpos'] = 0
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
	json = graphToDict(transactionGraph(pizza_address))
	print json

	mtgox_address = Address('1eHhgW6vquBYhwMPhQ668HPjxTtpvZGPC')
	json = graphToDict(transactionGraph(mtgox_address))
	print json