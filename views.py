from flask import render_template
from flask import request,jsonify
import json,os
from BitCrumbs import app
import pymysql as mdb
from transaction_graph2 import TransactionGraph

con = mdb.connect('localhost','root','','bitcoin')

@app.route('/')
@app.route('/index')
def index():
	return render_template("index.html")

@app.route('/bitcoinFlow')
def bitcoinFlow():
	address = request.args.get('address', 'error', type=str)
	#print address.split(',') 
	graph = TransactionGraph()
	graph.addSourceAddress(address.split(',')[0])
	result = jsonify(graph.toDict())
	graph.clear()
	return result

@app.route('/addresses')
def addresses():
	with con:
		cur = con.cursor()
		address_query = request.args.get('q','',type=str)
		command = 'SELECT DISTINCT address FROM tx_outputs '
		command += 'WHERE spendHash NOT LIKE "Unspent" '
		command += 'AND value > 10000 '
		command += 'AND address LIKE "%s%%" LIMIT 10' % address_query
		cur.execute(command)
		results = cur.fetchall()
	
	address_list = []
	for result in results:
		address_list.append({'id':result[0],'name':result[0]})
	return json.dumps(address_list)

