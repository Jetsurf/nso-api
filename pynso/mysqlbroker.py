from mysql.connector import pooling

class mysql_broker():
	def __init__(self, host, user, pw, db):
		self.__host = host
		self.__user = user
		self.__pw = pw
		self.__db = db
		self.pool = None
		self.cons = {}

	def startUp(self):
		self.pool = pooling.MySQLConnectionPool(pool_size=25, pool_reset_session=True, pool_name='py_nso', host=self.__host, database=self.__db, user=self.__user, password=self.__pw)
		print("MYSQL: Created connection pool")

	def connect(self):
		con = self.pool.get_connection()
		cur = con.cursor()
		self.cons[hash(cur)] = con
		return cur

	def c_commit(self, cur):
		self.cons[hash(cur)].commit()

	def c_rollback(self, cur):
		self.cons[hash(cur)].rollback()

	def commit(self, cur):
		self.cons[hash(cur)].commit()
		self.close(cur)

	def rollback(self, cur):
		self.cons[hash(cur)].rollback()
		self.close(cur)

	def getColumnNames(self, cur):
		return [col[0] for col in cur.description]

	def rowToDict(self, colnames, row):
		return dict(zip(colnames, row))

	def hasTable(self, cur, tablename):
		cur.execute("SELECT 1 FROM information_schema.TABLES WHERE (TABLE_SCHEMA = %s) AND (TABLE_NAME = %s) LIMIT 1", (self.__db, tablename))
		row = cur.fetchone()
		self.c_commit(cur)
		if row == None:
			return False
		return True

	def hasColumn(self, cur, tablename, columnname):
		cur.execute("SELECT 1 FROM information_schema.COLUMNS WHERE (TABLE_SCHEMA = %s) AND (TABLE_NAME = %s) AND (COLUMN_NAME = %s) LIMIT 1", (self.__db, tablename, columnname))
		row = cur.fetchone()
		self.c_commit(cur)
		if row == None:
			return False
		return True

	def hasKey(self, cur, tablename, keyname):
		cur.execute("SELECT * FROM information_schema.STATISTICS WHERE (TABLE_SCHEMA = %s) AND (TABLE_NAME = %s) AND (COLUMN_NAME = %s)", (self.__db, tablename, keyname,))
		row = cur.fetchone()
		self.c_commit(cur)
		if row == None:
			return False
		return True

	def getConnection(self, cur):
		return self.cursors[hash(cur)]

	def close(self, cur):
		con = self.cons[hash(cur)]
		cur.close()
		con.close()
		self.cons.pop(hash(cur))

	def close_pool(self):
		self.pool.close()
		self.pool.wait_closed()
		print("MYSQL: Closed Pool")
