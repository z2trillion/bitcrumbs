from flask import render_template
from flask import request,jsonify
import json,os
from BitCrumbs import app
import pymysql as mdb
from connect_by_transaction import transactionGraph, graphToDict2

@app.route('/')
@app.route('/index')
def index():
	return render_template("index.html")
	#return render_template('d3_test.html')
@app.route('/bitcoinFlow')
def bitcoinFlow():
	address = request.args.get('address','',type=str)
	graph = graphToDict2(transactionGraph(address))
	return jsonify(graph)

@app.route('/addresses')
def addresses():
	con = mdb.connect('localhost','root','','bitcoin')
	cur = con.cursor()
	address_query = request.args.get('q','',type=str)
	command = 'SELECT DISTINCT address FROM outputs '
	command += 'WHERE spendHash NOT LIKE "0000000000%%" '
	command += 'AND address LIKE "%s%%" LIMIT 10' % address_query
	# sort by address input/outout?
	cur.execute(command)
	results = cur.fetchall()
	address_list = []
	for result in results:
		address_list.append({'id':result[0],'name':result[0]})
	return json.dumps(address_list)

