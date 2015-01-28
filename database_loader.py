import bitcoin_tools as bt
import pymysql as mdb

NULL_HASH = 64*'0'
con = mdb.connect('localhost','root','','bitcoin') #host, user, password, #database

with con:
	cur = con.cursor()
	cur.execute('CREATE TABLE IF NOT EXISTS outputs ('+
              'transactionHash CHAR(64),'+
              'outputIndex INT, PRIMARY KEY (transactionHash,outputIndex),'+
						  'value BIGINT,'+
						  'blockNumber int,'+
						  'spendHash CHAR(64), INDEX (spendHash),'+
						  'address VARCHAR(35), INDEX (address))')
	cur.execute('CREATE TABLE IF NOT EXISTS blocks ('+
							'hash CHAR(64) PRIMARY KEY,'+ 
							'height INT)')

bc = bt.BlockChain()
for height,block in enumerate(bc):
	if height % 1e3 == 0:
		print height
	elif height > 2.5e5:
		break
	with con:
		cur = con.cursor()
		cur.execute("SELECT COUNT(*) FROM blocks WHERE hash = '%s'"%block.hash)
		if cur.fetchone()[0] == 1:
			continue
		for i,transaction in enumerate(block):
			if i > 0:
				for inTx in transaction.inputs:
					command = "UPDATE outputs SET spendHash = '%s' WHERE transactionHash = '%s' AND outputIndex = %i"
					command = command % (transaction.hash,inTx.tx_hash,inTx.tx_index)
					cur.execute(command)
			for index,outTx in enumerate(transaction.outputs):
				command = "INSERT IGNORE INTO outputs VALUES ('%s',%i,%i,'%s','%s','%s')" 
				command = command%(transaction.hash,index,outTx.value,height,NULL_HASH,outTx.address)
				cur.execute(command)
		cur.execute("INSERT INTO blocks VALUES ('%s',%i)"%(block.hash,height))

