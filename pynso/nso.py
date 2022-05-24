from .authentication import nso_authentication
from .s2_api import Splatoon2
from .mysqlbroker import mysql_broker
class NSO():
	def __init__(self, *args, **options):
		if options.get('bot_mode') if options.get('bot_mode') != None else False:
			print("pynso: Using bot mode")
			self.sql_pool = mysql_broker(options.get("db_host"), options.get("db_user"), options.get("db_pass"), options.get("db_name"))
			self.sql_pool.startUp()
			self.auth = nso_authentication(pynso_pool=self.sql_pool)
		else:
			print("pynso: Normal Mode")

		self.s2_api = Splatoon2(auth=self.auth)