import time
import requests
import re

from .nso_expiring_token import NSO_Expiring_Token

class NSO_API_S2:
	def __init__(self, nso_api):
		self.nso_api = nso_api
		self.game_id = 5741031244955648  # Splatoon 2
		self.web_service_token = None
		self.iksm_session_token = None
		self.xid = None

	def get_keys(self):
		keys = {}
		keys['web_service_token'] = self.web_service_token.to_hash() if self.web_service_token else None
		keys['iksm_session_token'] = self.iksm_session_token.to_hash() if self.iksm_session_token else None
		keys['x-unique-id'] = self.xid
		return keys

	def set_keys(self, keys):
		if not keys:
			return
		self.web_service_token = NSO_Expiring_Token.from_hash(keys['web_service_token']) if keys.get('web_service_token') else None
		self.iksm_session_token = NSO_Expiring_Token.from_hash(keys['iksm_session_token']) if keys.get('iksm_session_token') else None
		self.xid = keys.get['x-unique-id'] if keys.get('x-unique-id') else None

	def create_iksm_session_token_request(self):
		if not self.web_service_token:
			raise Exception("No web_service_token")

		headers = {}
		headers['Host'] = 'app.splatoon2.nintendo.net'
		headers['User-Agent'] = f'com.nintendo.znca/{self.nso_api.app_version} (Android/7.1.2)'
		headers['Content-Type'] = 'application/json; charset=utf-8'
		headers['X-Platform'] = 'Android'
		headers['X-ProductVersion'] = self.nso_api.app_version
		headers['x-gamewebtoken'] = self.web_service_token.value
		headers['x-isappanalyticsoptedin'] = 'false'
		headers['X-Requested-With'] = 'com.nintendo.znca'
		headers['Connection'] = 'keep-alive'

		req = requests.Request('GET', 'https://app.splatoon2.nintendo.net', headers = headers)
		return req

	def ensure_web_service_token(self):
		if self.web_service_token and self.web_service_token.is_fresh():
			return True

		web_service_token = self.nso_api.get_web_service_token(self.game_id)
		if not web_service_token:
			return False

		self.web_service_token = web_service_token
		self.nso_api.notify_keys_update()
		return True

	# Gets the iksm_session_token. This is actually an HTTP cookie.
	def ensure_iksm_session_token(self):
		if self.iksm_session_token and self.iksm_session_token.is_fresh():
			return True

		response = self.nso_api.do_http_request(self.create_iksm_session_token_request())
		if not response:
			return False

		iksm_session_token = None
		for cookie in response.cookies:
			if cookie.name == 'iksm_session':
				iksm_session_token = NSO_Expiring_Token(cookie.value, expiretime = cookie.expires)

		if not iksm_session_token:
			self.nso_api.errors.append("Expected iksm_session cookie but didn't get one")
			return False

		data = re.search("data-unique-id=\"([0-9]*?)\"", response.text)
		xid = data.group(0)
		if not xid:
			self.nso_api.errors.append("Expected data-unique-id, got none")
			return False

		self.xid = xid
		self.iksm_session_token = iksm_session_token
		self.nso_api.notify_keys_update()
		return True

	def get_player_json(self, url, referer = None):
		if not self.ensure_web_service_token():
			self.nso_api.errors.append("Could not get S2 web_service_token")
			return None

		if not self.ensure_iksm_session_token():
			self.nso_api.errors.append("Could not get S2 iksm_session_token")
			return None

		headers = {}
		headers['Host'] = 'app.splatoon2.nintendo.net'
		headers['x-requested-with'] = 'XMLHttpRequest'
		headers['x-unique-id'] = self.xid
		headers['x-timezone-offset'] = str(int((time.mktime(time.gmtime()) - time.mktime(time.localtime()))/60))
		headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36'
		headers['Accept'] = '*/*'
		headers['Referer'] = referer or 'https://app.splatoon2.nintendo.net/home'
		headers['Accept-Encoding'] = 'gzip, deflate'
		headers['Accept-Language'] = 'en-us'

		req = requests.Request('GET', url, headers = headers, cookies = dict(iksm_session = self.iksm_session_token.value))
		return self.nso_api.do_json_request(req)

	def post_store_json(self, merchid, confirmation):
		if not self.ensure_web_service_token():
			self.nso_api.errors.append("Could not get S2 web_service_token")
			return None

		if not self.ensure_iksm_session_token():
			self.nso_api.errors.append("Could not get S2 iksm_session_token")
			return None

		headers = {}
		headers['Origin'] = 'https://app.splatoon2.nintendo.net'
		headers['x-requested-with'] = 'XMLHttpRequest'
		headers['x-unique-id'] = self.xid
		headers['x-timezone-offset'] = str(int((time.mktime(time.gmtime()) - time.mktime(time.localtime()))/60))
		headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36'
		headers['Accept'] = '*/*'
		headers['Referer'] = f"https://app.splatoon2.nintendo.net/home/shop/{merchid}"
		headers['Accept-Encoding'] = 'gzip, deflate, br'
		headers['Accept-Language'] = 'en-us'

		if confirmation:
			payload = { "override" : 1 }
		else:
			payload = { "override" : 0 }

		f"https://app.splatoon2.nintendo.net/api/onlineshop/merchandises/{merchid}"
		req = requests.Request('POST', url, headers = headers, cookies = dict(iksm_session = self.iksm_session_token.value), data=payload)
		return self.nso_api.do_json_request(req)

	def do_records_request(self):
		return self.get_player_json("https://app.splatoon2.nintendo.net/api/records")

	def get_all_battles(self):
		return self.get_player_json("https://app.splatoon2.nintendo.net/api/results")	

	def get_full_battle(self, battleid):
		return self.get_player_json(f"https://app.splatoon2.nintendo.net/api/results/{battleid}")

	def get_sr_records(self):
		return self.get_player_json("https://app.splatoon2.nintendo.net/api/coop_results", "https://app.splatoon2.nintendo.net/coop")

	def post_store_purchase(self, merchid, confirmation=False):
		return self.post_store_json(merchid, confirmation)

	def get_ranks(self):
		records = self.do_records_request()
		if not records:
			return

		name = records['records']['player']['nickname']
		szrank = records['records']['player']['udemae_zones']['name']
		if szrank == "S+":
			szrank += str(records['records']['player']['udemae_zones']['s_plus_number'])

		rmrank = records['records']['player']['udemae_rainmaker']['name']
		if rmrank == "S+":
			rmrank += str(records['records']['player']['udemae_rainmaker']['s_plus_number'])

		tcrank = records['records']['player']['udemae_tower']['name']
		if tcrank == "S+":
			tcrank += str(records['records']['player']['udemae_tower']['s_plus_number'])

		cbrank = records['records']['player']['udemae_clam']['name']
		if cbrank == "S+":
			cbrank += str(records['records']['player']['udemae_clam']['s_plus_number'])

		return {"SZ": szrank, "RM": rmrank, "TC": tcrank, "CB": cbrank}
