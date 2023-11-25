import time
import requests
import re
import json
from datetime import datetime

from .nso_expiring_token import NSO_Expiring_Token

class NSO_API_ACNH:
	def __init__(self, nso_api):
		self.nso_api = nso_api
		self.game_id = 4953919198265344  # ACNH
		self.web_service_token = None
		self.g_token = None
		self.park_session = None
		self.ac_bearer = None
		self.cache = {}

	def get_keys(self):
		keys = {}
		keys['web_service_token'] = self.web_service_token.to_hash() if self.web_service_token else None
		keys['g_token'] = self.g_token.to_hash() if self.g_token else None
		keys['park_session'] = self.park_session.to_hash() if self.park_session else None
		keys['ac_bearer'] = self.ac_bearer.to_hash() if self.ac_bearer else None
		return keys

	def set_keys(self, keys):
		if keys is None:
			return
		self.web_service_token = NSO_Expiring_Token.from_hash(keys['web_service_token']) if keys.get('web_service_token') else None
		self.g_token = NSO_Expiring_Token.from_hash(keys['g_token']) if keys.get('g_token') else None
		self.park_session = NSO_Expiring_Token.from_hash(keys['park_session']) if keys.get('park_session') else None
		self.ac_bearer = NSO_Expiring_Token.from_hash(keys['ac_bearer']) if keys.get('ac_bearer') else None

	def create_g_token_session_token_request(self):
		if not self.web_service_token:
			raise Exception("No web service token")

		headers = {}
		headers['Host'] = 'web.sd.lp1.acbaa.srv.nintendo.net'
		headers['User-Agent'] = f'com.nintendo.znca/{self.nso_api.get_app_version()} (Android/7.1.2)'
		headers['X-Platform'] = 'Android'
		headers['Content-Type'] = 'application/json; charset=utf-8'
		headers['X-ProductVersion'] = self.nso_api.get_app_version()
		headers['x-gamewebtoken'] = self.web_service_token.value
		headers['x-isappanalyticsoptedin'] = 'false'
		headers['DNT'] = '0'
		headers['X-Requested-With'] = 'com.nintendo.znca'
		headers['Connection'] = 'keep-alive'

		req = requests.Request('GET', 'https://web.sd.lp1.acbaa.srv.nintendo.net/?lang=en-US&na_country=US&na_lang=en-US', headers=headers)

		return req

	def create_park_session_token_request(self):
		if not self.g_token:
			raise Exception("No g_token")

		if not self.cache.get("users"):
			raise Exception("No cached users")

		headers = {}
		headers['Host'] = 'web.sd.lp1.acbaa.srv.nintendo.net'
		headers['Accept'] = 'application/json, text/plain, */*'
		headers['User-Agent'] = f'com.nintendo.znca/{self.nso_api.get_app_version()} (Android/7.1.2)'
		headers['Content-Type'] = 'application/json; charset=utf-8'
		headers['X-Blanco-Version'] = '2.1.0'
		headers['Referer'] = 'https://web.sd.lp1.acbaa.srv.nintendo.net/?lang=en-US&na_country=US&na_lang=en-US'
		headers['Origin'] = 'https://web.sd.lp1.acbaa.srv.nintendo.net'

		jsonbody = {}
		jsonbody['userId'] = self.cache['users'][0]['id']

		req = requests.Request('POST', 'https://web.sd.lp1.acbaa.srv.nintendo.net/api/sd/v1/auth_token', headers=headers, json = jsonbody, cookies=dict(_gtoken=self.g_token.value, _dnt='1'))
		return req

	def ensure_web_service_token(self):
		if self.web_service_token and self.web_service_token.is_fresh():
			return True

		web_service_token = self.nso_api.get_web_service_token(self.game_id)
		if not web_service_token:
			return False

		self.web_service_token = web_service_token
		self.nso_api.notify_user_data_update()
		return True

	def ensure_g_token(self):
		if self.g_token and not self.g_token.is_expired():
			return True

		response = self.nso_api.do_http_request(self.create_g_token_session_token_request())
		if not response:
			return False

		g_token = None
		for cookie in response.cookies:
			if cookie.name == '_gtoken':
				if cookie.expires:
					g_token = NSO_Expiring_Token(cookie.value, expiretime = int(cookie.expires))
				else:
					g_token = NSO_Expiring_Token(cookie.value, expiretime = int(time.time() + (3600 * 6)))

		if not g_token:
			self.nso_api.errors.append("Expected _gtoken but didn't get one")
			return False

		self.g_token = g_token
		self.nso_api.notify_user_data_update()
		return True

	# Gets park_session and ac_bearer tokens.
	def ensure_park_session_token(self):
		if self.park_session and self.park_session.is_fresh() and self.ac_bearer and self.ac_bearer.is_fresh():
			return True

		response = self.nso_api.do_http_request(self.create_park_session_token_request(), expect_status = [201])  # Successful response status is "201 Created"
		if not response:
			return False

		park_session = None
		for cookie in response.cookies:
			if cookie.name == '_park_session':
				if cookie.expires:
					park_session = NSO_Expiring_Token(cookie.value, expiretime = int(cookie.expires))
				else:
					park_session = NSO_Expiring_Token(cookie.value, expiretime = int(time.time() + (3600 * 6)))

		if not park_session:
			self.nso_api.errors.append("Expected park_session, got none")
			return False

		data = json.loads(response.text)
		if not data.get('token'):
			self.nso_api.errors.append("Expected ac_bearer, got none")
			return False

		ac_bearer = NSO_Expiring_Token(data['token'], expiretime = data['expireAt'])

		self.park_session = park_session
		self.ac_bearer = ac_bearer
		self.nso_api.notify_user_data_update()
		return True

	# Ensures we have the "users" data cached.
	def ensure_users_data(self):
		if self.cache.get("users"):
			return True

		if not self.get_users_json():
			return False

		return True

	def ensure_tokens(self):
		if not self.ensure_web_service_token():
			return False
		if not self.ensure_g_token():
			return False
		if not self.ensure_users_data():  # Not technically a token but needed to get the park_session and ac_bearer
			return False
		if not self.ensure_park_session_token():
			return False

		return True

	def get_users_json(self):
		if not self.ensure_web_service_token():
			self.nso_api.errors.append("Could not get ACNH web_service_token")
			return None

		if not self.ensure_g_token():
			self.nso_api.errors.append("Could not get ACNH tokens")
			return None

		headers = {}
		headers['Host'] = 'web.sd.lp1.acbaa.srv.nintendo.net'
		headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36'
		headers['Accept'] = 'application/json, text/plain, */*'
		headers['Referer'] = 'https://web.sd.lp1.acbaa.srv.nintendo.net/?lang=en-US&na_country=US&na_lang=en-US'
		headers['Accept-Language'] = 'en-us'
		headers['Accept-Encoding'] = 'gzip, deflate, br'

		req = requests.Request('GET', 'https://web.sd.lp1.acbaa.srv.nintendo.net/api/sd/v1/users', headers=headers, cookies=dict(_gtoken=self.g_token.value, _dnt='1'))
		#Done to cache a copy for land id and user id
		json = self.nso_api.do_json_request(req)
		if json:
			self.cache['users'] = json['users']
		return json

	#Any "Authed" endpoints require park_session and bearer tokens
	def get_authed_json(self, url, referer=None):
		if not self.ensure_web_service_token():
			self.nso_api.errors.append("Could not get ACNH web_service_token")
			return None

		if not self.ensure_tokens():
			self.nso_api.errors.append("Could not get ACNH tokens")
			return None

		headers = {}
		headers['Host'] = 'web.sd.lp1.acbaa.srv.nintendo.net'
		headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36'
		if not referer:
			headers['Referer'] = 'https://web.sd.lp1.acbaa.srv.nintendo.net/players/passport'
		else:
			headers['Referer'] = referer
		headers['Authorization'] = f"Bearer {self.ac_bearer.value}"
		headers['Accept-Language'] = 'en-us'
		headers['Accept-Encoding'] = 'gzip, deflate, br'

		req = requests.Request('GET', url, headers=headers, cookies=dict(_gtoken=self.g_token.value, _park_session=self.park_session.value, _dnt='1'))
		return self.nso_api.do_json_request(req)

	def get_detailed_user_json(self):
		return self.get_authed_json(f"https://web.sd.lp1.acbaa.srv.nintendo.net/api/sd/v1/users/{self.cache['users'][0]['id']}/profile?language=en-US")

	def get_lands_json(self):
		return self.get_authed_json(f"https://web.sd.lp1.acbaa.srv.nintendo.net/api/sd/v1/lands/{self.cache['users'][0]['land']['id']}/profile?language=en-US")

	def post_message(self, referrer, body):
		if not self.ensure_web_service_token():
			self.nso_api.errors.append("Could not get ACNH web_service_token")
			return None

		if not self.ensure_tokens():
			self.nso_api.errors.append("Could not get ACNH tokens")
			return None

		headers = {}
		headers['Host'] = 'web.sd.lp1.acbaa.srv.nintendo.net'
		headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36'
		headers['Referer'] = referrer
		headers['Authorization'] = f"Bearer {self.ac_bearer.value}"
		headers['Accept-Language'] = 'en-us'
		headers['Accept-Encoding'] = 'gzip, deflate, br'

		req = requests.Request('POST', 'https://web.sd.lp1.acbaa.srv.nintendo.net/api/sd/v1/messages', json=body, headers=headers, cookies=dict(_gtoken=self.g_token.value, _park_session=self.park_session.value, _dnt='1'))
		#201 is success, 400 is bad request with code '3002', likely due to emote provided invalid, 403 is usually due to not being online in game with code '1001'
		return self.nso_api.do_json_request(req, expect_status=[201, 400, 403])

	def get_emotes(self):
		return self.get_authed_json("https://web.sd.lp1.acbaa.srv.nintendo.net/api/sd/v1/emoticons?language=en-US")

	def send_message(self, message):
		body = {}
		body['type'] = 'keyboard'
		body['body'] = message
		referrer = "https://web.sd.lp1.acbaa.srv.nintendo.net/players/chat"
		return self.post_message(referrer, body)

	#NOTE: You must have access to the emote to perform it, must match exactly what's returned from get_emotes
	#NOTE: It is best to check errors in your project, look at the comment 2 above to see how to handle this
	def send_emote(self, emote):
		body = {}
		body['type'] = 'emoticon'
		body['body'] = emote
		referrer = 'https://web.sd.lp1.acbaa.srv.nintendo.net/players/reaction'
		return self.post_message(referrer, body)

	def get_catalog_items_latest(self):
		return self.get_authed_json("https://web.sd.lp1.acbaa.srv.nintendo.net/api/sd/v1/catalog_items/latest")

	def get_catalog_items_favorites(self):
		return self.get_authed_json("https://web.sd.lp1.acbaa.srv.nintendo.net/api/sd/v1/catalog_items/favorites")

	def get_catalog_items(self):
		return self.get_authed_json(f"https://web.sd.lp1.acbaa.srv.nintendo.net/api/sd/v1/catalog_items?language=en-US&current_year={datetime.now().strftime('%Y')}")
