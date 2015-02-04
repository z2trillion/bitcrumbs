# fixes some bugs in database_loader
# - add incrementing id to keep track of tx order WITHIN blocks
# - store transactions hases in the right endianess

import sys
import bitcoin_tools as bt
import pymysql as mdb

blocks_table_name = 'blocks_hashes'
outputs_table_name = 'tx_outputs'

con = mdb.connect('localhost','root','','bitcoin') #host, user, password, #database

with con:
	cur = con.cursor()
	command = 'CREATE TABLE IF NOT EXISTS %s (' %outputs_table_name
	command += 'id BIGINT NOT NULL AUTO_INCREMENT, PRIMARY KEY (id), '
	command += 'transactionHash CHAR(64), INDEX(transactionHash), '
	command += 'outputIndex INT, '
	command += 'value BIGINT, '
	command += 'blockNumber INT, '
	command += 'spendHash CHAR(64), INDEX (spendHash), '
	command += 'address VARCHAR(35), INDEX (address))'
	cur.execute(command)

	command = 'CREATE TABLE IF NOT EXISTS %s ' %blocks_table_name
	command += '(blockHash CHAR(64) PRIMARY KEY, height INT)' 
	cur.execute(command)

# easier to flip here, at the end, for now.
def charFlipper(s):
	evens = s[::2]
	odds = s[1::2]
	reinterlaced = ''.join([o+e for e,o in zip(evens,odds)])
	return reinterlaced[::-1]

bc = bt.BlockChain()
for height,block in enumerate(bc):
	if height % 1e3 == 0:
		print height
	elif height > 2e5:
		break
	with con:
		cur = con.cursor()
		cur.execute("SELECT COUNT(*) FROM %s WHERE blockHash = '%s'" %(blocks_table_name, block.hash))
		if cur.fetchone()[0] == 1:
			continue
		for i,transaction in enumerate(block):
			transaction.hash = charFlipper(transaction.hash) # fix this deeper down later
			if i > 0: # to exclude the coinbase transaction
				for inTx in transaction.inputs:
					inTx.tx_hash = charFlipper(inTx.tx_hash)
					command = "UPDATE %s SET spendHash = '%s' WHERE transactionHash = '%s' AND outputIndex = %i"
					command = command % (outputs_table_name, transaction.hash, inTx.tx_hash, inTx.tx_index)
					cur.execute(command)
			for index,outTx in enumerate(transaction.outputs):
				command = "INSERT IGNORE INTO %s " %outputs_table_name
				command += "(transactionHash, outputIndex, value, blockNumber, spendHash, address) "
				command += "VALUES ('%s',%i,%i,'%s','%s','%s')" 
				command %= (transaction.hash,index,outTx.value,height,'Unspent',outTx.address)
				cur.execute(command)
		cur.execute("INSERT INTO %s VALUES ('%s',%i)" % (blocks_table_name, block.hash, height))

