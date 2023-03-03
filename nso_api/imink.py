# https://github.com/frozenpandaman/splatnet2statink/wiki/api-docs
import json, sys
import requests

class IMink:
	def __init__(self, user_agent):
		if user_agent == None:
			print("nso-api: User Agent for iMink is not present! Please set one with a method of contact from iMink.")
			#Can throw an assert, just temporary
			sys.exit(1)

		self.user_agent = user_agent
		self.session = requests.Session()

	def create_f_request(self, id_token, guid, method):
		api_app_head = {
			'Content-Type': 'application/json; charset=utf-8',
			'User-Agent' : self.user_agent
		}
		api_app_body = {
			'hash_method':  str(method),
			'request_id':   guid,
			'token': id_token,
		}

		req = requests.Request('POST', "https://api.imink.jone.wang/f", headers=api_app_head, data=json.dumps(api_app_body))
		return req

	def get_f(self, id_token, guid, method):
		req = self.create_f_request(id_token, guid, method)
		res = self.session.send(self.session.prepare_request(req))
		if res.status_code != 200:
			print(f'Unexpected HTTP code {res.status_code} from imink f')
			return None

		#print(f"nso-api: iMink: {res.text}")
		return res.json()

	def get_nso_f(self, id_token, guid):
		return self.get_f(id_token, guid, 1)

	def get_app_f(self, web_api_token, guid):
		return self.get_f(web_api_token, guid, 2)
