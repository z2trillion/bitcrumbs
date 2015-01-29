function fetchData(address) {
	$.ajax({
		type: "GET",
		url: '/bitcoinFlow',
		data: {'address' : address}
	})
	.done(function(data){
		if (data.length == 0) { 
			destroySankey();
		} else {
			renderSankey(data);
		}
	})
	.fail(function(data){
		console.log('Could not load json.',data);
	});
};

function destroySankey() {
	svg.selectAll("*").remove();
};

function renderSankey(graph) {
	sankey
		.nodes(graph.nodes)
		.links(graph.links)
		.layout(100);

	var link = svg.append("g").selectAll(".link")
		.data(graph.links)
		.enter().append("path")
		.attr("class", "link")
		.attr("d", path)
	    //.style("fill" , function(d) {return d3.rgb("#000");})
	    //  .style("stroke-width", function(d) { return Math.max(1, d.dy); })
	    .style("stroke-width", function(d) { return 1; })
	    .sort(function(a, b) { return b.dy - a.dy; });

	    link.append("title")
	    .text(function(d) { return d.source.name + " → " + d.target.name + "\n" + format(d.value); });

	var node = svg.append("g").selectAll(".node")
	    .data(graph.nodes)
	    .enter().append("g")
	    .attr("class", "node")
	    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
	    .call(d3.behavior.drag()
	    	.origin(function(d) { return d; })
	    	.on("dragstart", function() { this.parentNode.appendChild(this); })
	    	.on("drag", dragmove));

	node.append("rect")
	    .attr("height", function(d) { return d.dy; })
	    .attr("width", sankey.nodeWidth())
	    .attr("fill" , function (d) {return d3.scale.linear().domain([0,1]).range(["black","red"])(d.color);})
	    .append("title")
	    .text(function(d) { return d.color + "\n" + format(d.value); });

	function dragmove(d) {
		d3.select(this).attr("transform", "translate(" + d.x + "," + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ")");
		sankey.relayout();
		link.attr("d", path);
	}	
};

$(document).ready(function() {
	$(".address_input").select2({
	  	multiple: true,
	  	placeholder: "Address or Transaction",
	  	minimumInputLength: 1,
	  	ajax: {
	  		url: "/addresses",
	  		dataType: 'json',
	  		delay: 100,
	  		data: function (params) {
	  			return {q: params.term};
	  		},
	  		processResults: function (data, page) {
	  			return {results: data};
	  		},
	  		cache: true
	  	},
	  	templateResult: function (address) {
	  		return '<div>' + address.name + '</div>';
	  	},
	  	templateSelection: function (address) {
	  		return address.name;
	  	}
	});
	$(".address_input").on("change", function (e) {
	  	var addresses = $(".address_input").val();
	  	if (addresses == null){
	  		destroySankey();
	  	}
	  	else {
	  		fetchData(addresses[0]);
	  	}	 
	}); 
});