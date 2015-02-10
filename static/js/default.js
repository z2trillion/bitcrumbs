var windowHeight = $(window).height();
var windowWidth = $(window).width();

var margin = {top: 0, right: 50, bottom: 0, left: 0},
width = windowWidth - 50 - margin.right,
height = windowHeight - 250 - margin.bottom;

var formatNumber = d3.format(",.0f"),
format = function(d) { return formatNumber(d) + " TWh"; },
color = d3.scale.category20();

var svg = d3.select("#chart").append("svg")
	.attr("width", width + margin.left + margin.right)
	.attr("height", height + margin.top + margin.bottom)
    .append("g")
    .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

var sankey = d3.sankey()
	.nodeWidth(10)
	.nodePadding(10)
	.size([width, height]);

var path = sankey.link();

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
		.layout(32);

	var link = svg.append("g").selectAll(".link")
		.data(graph.links)
		.enter().append("path")
		.attr("class", "link")
		.attr("d", path)
	    //.style("stroke-width", function(d) { return 1; })
	    .sort(function(a, b) { return b.dy - a.dy; });

	    //link.append("title")
	    //.text(function(d) { return d.source.name + " → " + d.target.name + "\n" + format(d.value); });

	var node = svg.append("g")
		.selectAll(".node")
	    .data(graph.nodes)
	    .enter().append("g")
	    .attr("class", "node")
	    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
	    //.on("mouseover", nodeMouseover)
	    //.on("mouseout",nodeMouseout)
	    .call(d3.behavior.drag()
	    	.origin(function(d) { return d; })
	    	.on("dragstart", function() { this.parentNode.appendChild(this); })
	    	.on("drag", dragmove));

	node.append("rect")
		.attr("stroke-width", function(d){ return d.is_source})
	    .attr("height", function(d) { return d.dy; })
	    .attr("width", width)
	    .attr("fill" , coloring);
	function width(d) {
		if (d.is_source == 0) {
			return sankey.nodeWidth();
		} else {
			return sankey.nodeWidth();
		}; 
	};

	node.on("mouseover", nodeMouseover);

	//svg.selectAll(".rect")
	//	.on('mouseover',rectMouseover);
	//function rectMouseover(element) {
	//	console.log(element);
	//};
	
	//var myNodes = $(".node");

	function nodeMouseover(element) {
		information.find("#address").text(element.address);
		information.find("#transaction_hash").text(element.name);
		information.find("#taint").text( Math.round(100 * element.contamination / element.btc_value)+ '%');
		information.find("#value").text(element.btc_value);
		d3.selectAll('rect').attr("opacity",fadeFuture)
		d3.selectAll('.link').attr("opacity",fadeFuture)
		function fadeFuture(d) {
			if (d.time <= element.time) {
				return 1;
			} else {
				return .2;
			};
		};
	};

	node.append("rect")
		.attr("stroke-width", function(d){ return d.is_source})
	    .attr("height", function(d) { return d.dy; })
	    .attr("width", width)
	    .attr("fill" , coloring);
	function width(d) {
		if (d.is_source == 0) {
			return sankey.nodeWidth();
		} else {
			return sankey.nodeWidth();
		}; 
	};
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
	  	placeholder: "Enter bitcoin address here!",
	  	maximumSelectionLength: 1,
	  	minimumInputLength: 1,
	  	multiple: true,
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
			var s = addresses.reduce(function(x,y){return x+","+y;});
	  		fetchData(s);
	  	}	 
	}); 

	// 
});