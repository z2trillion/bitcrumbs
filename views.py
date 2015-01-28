from flask import render_template
from flask import request,jsonify
import json,os
from BitCrumbs import app
import pymysql as mdb
from connect_by_transaction import transactionGraph, graphToDict

@app.route('/')
@app.route('/index')
def index():
	address = 'hiiii'
	return render_template("index.html",address=address)
	return render_template('d3_test.html')
@app.route('/bitcoinFlow')
def bitcoinFlow():
	address = request.args.get('address','',type=str)
	graph = graphToDict(transactionGraph(address))
	return jsonify(graph)

@app.route('/addresses')
def addresses():
	con = mdb.connect('localhost','root','','bitcoin')
	cur = con.cursor()
	address_query = request.args.get('q','',type=str)
	command = 'SELECT DISTINCT address FROM outputs WHERE address LIKE "%s%%" LIMIT 10'
	command = command % address_query
	cur.execute(command)
	results = cur.fetchall()
	address_list = []
	for result in results:
		address_list.append({'id':result[0],'name':result[0]})
	return json.dumps(address_list)

