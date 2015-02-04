var information = $("#information")

function fetchData(address) {
	$.ajax({
		type: "GET",
		url: '/bitcoinFlow',
		data: {'address' : address}
	})
	.done(function(data){
		destroySankey();
		renderSankey(data);
	})
	.fail(function(data){
		console.log('Could not load json.',data);
	});
};

function clearInformation() {
	console.log('asdfasd')
	information.find("#address").text("\u0020");
	information.find("#transaction_hash").text("\u0020");
	information.find("#taint").text("\u0020");
	information.find("#value").text("\u0020");
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
	    .style("stroke-width", function(d) { return 1; })
	    .sort(function(a, b) { return b.dy - a.dy; });

	    //link.append("title")
	    //.text(function(d) { return d.source.name + " → " + d.target.name + "\n" + format(d.value); });

	var node = svg.append("g")
		.selectAll(".node")
	    .data(graph.nodes)
	    .enter().append("g")
	    .attr("class", "node")
	    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
	    .on("mouseover", nodeMouseover)
	    //.on("mouseout",nodeMouseout)
	    .call(d3.behavior.drag()
	    	.origin(function(d) { return d; })
	    	.on("dragstart", function() { this.parentNode.appendChild(this); })
	    	.on("drag", dragmove));
	
	function nodeMouseover(element) {
		information.find("#address").text(element.address);
		information.find("#transaction_hash").text(element.name);
		information.find("#taint").text(element.color);
		information.find("#value").text("\u0e3f " + element.btc_value);
		//x = element.x + 120
		//y = d3.event.pageY - 25
		//information.css({left: x, top: y});
		information.toggleClass("hidden",false);
	};

	node.append("rect")
	    .attr("height", function(d) { return d.dy; })
	    .attr("width", sankey.nodeWidth())
	    .attr("fill" , coloring);
	function coloring(d) {
		return d.color
	};
	function dragmove(d) {
		d3.select(this).attr("transform", "translate(" + d.x + "," + (d.y = Math.max(0, Math.min(height - d.dy, d3.event.y))) + ")");
		sankey.relayout();
		link.attr("d", path);
	};	
};

$(document).ready(function() {
	$(".address_input").select2({
	  	multiple: true,
	  	placeholder: "Address or Transaction",
	  	maximumSelectionLength: 2,
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
	  		clearInformation();
	  	}
	  	else {
	  		//console.log(addresses+"asd.fljasld;kjfal;skd");
			var s = addresses.reduce(function(x,y){return x+","+y;});
			//console.log(s);
	  		fetchData(s);
	  	}	 
	}); 
});