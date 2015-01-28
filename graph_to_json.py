def graphToDict(graph):
	node_names = set([line[0] for line in graph])
	node_names |= set([line[1] for line in graph])
	node_names = list(node_names)

	weights = {}
	for line in graph:
		weights[line[0]] = line[-1]
		weights[line[1]] = line[-1]

	node_index_map = {name:i for i,name in enumerate(node_names)}
	nodes = [{'name':name[:10],'color':weights[name]} for name in node_names]

	edges = []
	for line in graph:
		source = node_index_map[line[0]]
		sink = node_index_map[line[1]]
		edge = {'source':source,'target':sink,'value':line[2]}
		edges.append(edge)
	return {'nodes':nodes,'links':edges}

