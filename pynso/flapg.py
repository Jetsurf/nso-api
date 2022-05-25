# https://github.com/frozenpandaman/splatnet2statink/wiki/api-docs
import json
import requests

class Flapg:
	def __init__(self, user_agent):
		self.user_agent = user_agent
		self.session = requests.Session()

	def create_hash_request(self, id_token, timestamp):
		headers = {}
		headers['User-Agent'] = self.user_agent
		headers['Accept'] = 'application/json'

		data = {}
		data['naIdToken'] = id_token
		data['timestamp'] = timestamp

		req = requests.Request('POST', 'https://elifessler.com/s2s/api/gen2', headers=headers, data=data)
		return req

	def create_f_request(self, id_token, guid, hash, timestamp, iid):
		headers = {}
		headers['User-Agent'] = self.user_agent
		headers['Accept'] = 'application/json'
		headers['x-token'] = id_token
		headers['x-time'] = str(timestamp)
		headers['x-guid'] = guid
		headers['x-hash'] = hash
		headers['x-ver'] = str(3)
		headers['x-iid'] = iid

		req = requests.Request('GET', 'https://flapg.com/ika2/api/login?public', headers=headers)
		return req

	def get_f(self, id_token, guid, timestamp, iid):
		req = self.create_hash_request(id_token, timestamp)
		res = self.session.send(self.session.prepare_request(req))
		if res.status_code != 200:
			print(f'Unexpected HTTP code {res.status_code} from flapg hash')
			return None

		#print(res.text)
		hash = res.json()['hash']
		#print(f'Hash is: {hash}')

		req = self.create_f_request(id_token, guid, hash, timestamp, iid)
		res = self.session.send(self.session.prepare_request(req))
		if res.status_code != 200:
			print(f'Unexpected HTTP code {res.status_code} from flapg f')
			return None

		#print("FLAPG: " + res.text)
		return res.json()['result']['f']

	def get_nso_f(self, id_token, guid, timestamp):
		return self.get_f(id_token, guid, timestamp, 'nso')

	def get_app_f(self, web_api_token, guid, timestamp):
		return self.get_f(web_api_token, guid, timestamp, 'app')
