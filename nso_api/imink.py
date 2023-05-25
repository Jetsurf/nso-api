# https://github.com/JoneWang/imink/wiki/imink-API-Documentation
import json, sys
import requests

class IMink:
	DEFAULT_URL = "https://api.imink.jone.wang/f"

	def __init__(self, user_agent, url = DEFAULT_URL):
		if user_agent == None:
			print("nso-api: User Agent for iMink is not present! Please set one with a method of contact from iMink.")
			#Can throw an assert, just temporary
			sys.exit(1)

		self.user_agent = user_agent
		self.url = url
		self.session = requests.Session()

	def create_f_request(self, id_token, guid, method, nsaid):
		api_app_head = {
			'Content-Type': 'application/json; charset=utf-8',
			'User-Agent' : self.user_agent
		}
		api_app_body = {
			'hash_method':  str(method),
			'request_id':   guid,
			'token': id_token,
			'na_id': nsaid
		}

		req = requests.Request('POST', self.url, headers=api_app_head, data=json.dumps(api_app_body))
		return req

	def get_f(self, method, id_token, guid, nsaid):
		req = self.create_f_request(id_token, guid, method, nsaid)
		res = self.session.send(self.session.prepare_request(req))
		if res.status_code != 200:
			print(f'Unexpected HTTP code {res.status_code} from imink f')
			return None

		#print(f"nso-api: iMink: {res.text}")
		return res.json()

	def get_nso_f(self, id_token, guid, nsaid):
		return self.get_f(1, id_token, guid, nsaid)

	def get_app_f(self, web_api_token, guid, nsaid):
		return self.get_f(2, web_api_token, guid, nsaid)
