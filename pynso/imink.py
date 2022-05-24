# https://github.com/frozenpandaman/splatnet2statink/wiki/api-docs
import json
import requests

class IMink:
	def __init__(self):
		self.user_agent = 'Test proof of concept/0.1 (awendt@putergeek.com)'
		self.session = requests.Session()

	def create_f_request(self, id_token, guid, timestamp, method):
		api_app_head = {
			'Content-Type': 'application/json; charset=utf-8',
			#TODO: Make this user agent send bot owner, not my hardcoded id
			'User-Agent' : 'Jet-bot/1.0.0 (discord=jetsurf#8514)'
		}
		api_app_body = {
			'hash_method':  str(method),
			'request_id':   guid,
			'token': id_token,
			'timestamp':  str(timestamp),
		}

		req = requests.Request('POST', "https://api.imink.jone.wang/f", headers=api_app_head, data=json.dumps(api_app_body))
		return req

	def get_f(self, id_token, guid, timestamp, method):
		req = self.create_f_request(id_token, guid, timestamp, method)
		res = self.session.send(self.session.prepare_request(req))
		if res.status_code != 200:
			print(f'Unexpected HTTP code {res.status_code} from imink f')
			return None

		print(f"pynso: iMink: {res.text}")
		return res.json()['f']

	def get_nso_f(self, id_token, guid, timestamp):
		return self.get_f(id_token, guid, timestamp, 1)

	def get_app_f(self, web_api_token, guid, timestamp):
		return self.get_f(web_api_token, guid, timestamp, 2)
