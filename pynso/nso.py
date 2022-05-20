from mysql.connector import pooling
import authentication
import s2_api

class NSO():
	def __init__(self, *args, **options):
		if options.get('bot_mode') if options.get('bot_mode') != None else False:
			print("pynso: Using bot mode")
			self.con_pool = pooling.MySQLConnectionPool(pool_name="pynso_pool",
                                                  	pool_size=10,
                                                  	pool_reset_session=True,
                                                  	host=options.get("db_host"),
                                                  	database=options.get("db_name"),
                                                  	user=options.get("db_user"),
                                                  	password=options.get("db_pass"))
			self.auth = authentication.nso_authentication(pynso_pool=self.con_pool)

		else:
			print("pynso: Normal Mode")

		self.s2_api = s2_api.Splatoon2(self.auth)