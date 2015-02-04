import heapq, sys
import numpy as np
from bitcoin_classes import Address, Transaction, Coins



class HeapSet:
	def __init__(self, min_heap = True):
		self.heap = []
		self.elements = set([])
		self.min_heap = min_heap
	def add(self,tx):
		if tx not in self.elements:
			self.elements.add(tx)
			if self.min_heap:
				priority = tx.height()
			else:
				priority = -tx.height()
			heapq.heappush(self.heap, (priority, tx))
	def pop(self):
		priority, tx = heapq.heappop(self.heap)
		self.elements.remove(tx)
		return priority, tx
	def __len__(self):
		return len(self.heap)

class TransactionGraph:	
	def __init__(self):
		self.nodes = set([])
		self.edges = set([])

	def addSourceAddress(self, address_string, index = 0):
		address = Address(address_string)
		self.backwardInTime(address)
		#self.forwardInTime(address, index)

	def seedOutputs(self,address,direction,index):
		if direction == 'forward':
			contaminated_coins = HeapSet(min_heap = True)
		else:
			contaminated_coins = HeapSet(min_heap = False)
		total_contamination = 0

		n_outputs = len(address.outputs())
		for i, output in enumerate(address.outputs()):
			output.contamination = np.zeros(n_outputs)
			output.contamination[i] = output.value
			total_contamination += output.value
			output.is_source = True
			contaminated_coins.add(output)
		return contaminated_coins, total_contamination		

	def backwardInTime(self, address):
		contaminated_txs = HeapSet(min_heap = False)
		total_contamination = 0

		n_outputs = address.countInputs()

		for i, input in enumerate(address.inputs()):
			if i == 36:
				input.contamination = input.value
				contaminated_txs.add(input.transaction)
			else:
				input.contamination = 0
			total_contamination +=  input.value
		
		while len(contaminated_txs) > 0:
			height, tx = contaminated_txs.pop()

			tx_contamination = 0			
			for output in tx.outputs():
				tx_contamination += output.contamination
			total_input = tx.inputValue()

			#print total_contamination

			#if tx_contamination < (total_contamination / 1e100):
			#	continue
			#elif tx_contamination / total_input < 0:#.00000000001:
			#	continue

			#print tx, tx_contamination, total_input
			print -height, tx
			for input in tx.inputs():
				#print input.contamination
				weight = input.value / total_input
				assert weight <= 1
				assert input.contamination == 0
				input.contamination += weight * tx_contamination
				contaminated_txs.add(input.transaction)
				assert input.contamination <= input.value

		
		

	def forwardInTime(self, address, index):
		contaminated_coins, total_contamination = self.seedOutputs(address,'forward',index)

		while len(contaminated_coins) > 0 and len(self.nodes) < 1000:
			height, coins = contaminated_coins.pop()

			if coins.contamination[index] < total_contamination / 100:
				continue
			elif coins.forward_taint(index) < 0.01:
				continue
			else:
				self.addNode(coins)
				print coins
			if coins.notSpent():
				continue

			total_input_value = float(coins.spend_transaction.inputValue())
			total_output_value = 0
			for next_coins in coins.nextOutputs():
				weight = next_coins.value / total_input_value
				additional_contamination = weight * coins.contamination
				next_coins.contamination += additional_contamination	
				if next_coins.contamination[index] > next_coins.value:
					next_coins.contamination[index] = next_coins.value
				
				contaminated_coins.add(next_coins)
				coins.addSink(next_coins,additional_contamination)

	def addNode(self,node):
		self.nodes.add(node)

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
	#pizza_address = '17SkEw2md5avVNyYgj6RiXuQKNwkXaxFyQ'
	#g = TransactionGraph()
	#g.addSourceAddress(pizza_address)

	mtgox_address = '1eHhgW6vquBYhwMPhQ668HPjxTtpvZGPC'
	g = TransactionGraph()
	g.addSourceAddress(mtgox_address)
	#g.connectEdges()