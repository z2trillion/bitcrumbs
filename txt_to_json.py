def toJson(graph):
	nodes = {}
	node_names = []
	edges = []
	for line in graph:
		source = line[0]
		sink = line[1]
		try: 
			source = nodes[source]
		except KeyError:
			node_names.append(source)
			nodes[source] = len(node_names)-1
			source = nodes[source]
		try:
			sink = nodes[sink]
		except KeyError:
			node_names.append(sink)
			nodes[sink] = len(node_names)-1
			sink = nodes[sink]
		amount = float(line[2])
		taint = float(line[3])
		edges.append([source,sink,amount/1e8,taint])

	print '{"nodes":['
	for i,node in enumerate(node_names):
		if i != 0:
			print ',',
		print '{"name":"%s"}' % node[:10]
	print '],'
	print '"links":['
	for i,edge in enumerate(edges):
		if i != 0:
			print ',',
		print '{"source":%i,"target":%i,"value":%f}' %tuple(edge[:3])
	print ']}'

