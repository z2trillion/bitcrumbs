# fixes some bugs in database_loader
# - add incrementing id to keep track of tx order WITHIN blocks
# - store transactions hases in the right endianess

import sys
import bitcoin_tools as bt
import pymysql as mdb

con = mdb.connect('localhost','root','','bitcoin') #host, user, password, #database

with con:
	cur = con.cursor()
	command = 'CREATE TABLE IF NOT EXISTS tx_outputs ('
	command += 'id BIGINT NOT NULL AUTO_INCREMENT, PRIMARY KEY (id), '
	command += 'transactionHash CHAR(64), INDEX(transactionHash), '
	command += 'outputIndex INT, '
	command += 'value BIGINT, '
	command += 'blockNumber INT, '
	command += 'spendHash CHAR(64), INDEX (spendHash), '
	command += 'address VARCHAR(35), INDEX (address))'
	cur.execute(command)

	cur.execute('CREATE TABLE IF NOT EXISTS block_hashes ('+
							'blockHash CHAR(64) PRIMARY KEY,'+ 
							'height INT)')

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
	elif height > 2.5e5:
		break
	with con:
		cur = con.cursor()
		cur.execute("SELECT COUNT(*) FROM block_hashes WHERE blockHash = '%s'"%block.hash)
		if cur.fetchone()[0] == 1:
			continue
		for i,transaction in enumerate(block):
			transaction.hash = charFlipper(transaction.hash) # fix this deeper down later
			if i > 0: # to exclude the coinbase transaction
				for inTx in transaction.inputs:
					command = "UPDATE outputs SET spendHash = '%s' WHERE transactionHash = '%s' AND outputIndex = %i"
					command = command % (transaction.hash,inTx.tx_hash,inTx.tx_index)
					cur.execute(command)
			for index,outTx in enumerate(transaction.outputs):
				command = "INSERT IGNORE INTO tx_outputs "
				command += "(transactionHash, outputIndex, value, blockNumber, spendHash, address) "
				command += "VALUES ('%s',%i,%i,'%s','%s','%s')" 
				command %= (transaction.hash,index,outTx.value,height,'Unspent',outTx.address)
				cur.execute(command)
		cur.execute("INSERT INTO block_hashes VALUES ('%s',%i)" % (block.hash, height))

