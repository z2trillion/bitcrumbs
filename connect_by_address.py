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
	contaminated_outputs = PrioritySet()
	contaminated_txs = {}
	for tx in source_address.outgoingTxs():
		for output in tx.outputs():
			output.contamination = float(output.value)
			contaminated_outputs.add(output)
	while len(contaminated_outputs) > 0:
		height, oldest_output = contaminated_outputs.pop()
		if oldest_output.spend_transaction == str(None):
			print 'Unspent Output:', oldest_output
			continue
		elif oldest_output.contamination < 10e10:
			continue
		else:
			print oldest_output
		for connected_output in oldest_output.spend_transaction.outputs():
			contaminated_outputs.add(connected_output)
			weight = float(connected_output.value / oldest_output.spend_transaction.inputValue())
			contaminated_outputs[connected_output].contamination += weight * oldest_output.contamination

if __name__ == '__main__':
	pizza_address = Address('17SkEw2md5avVNyYgj6RiXuQKNwkXaxFyQ')
	transactionGraph(pizza_address)
