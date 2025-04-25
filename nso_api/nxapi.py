import json, sys, os
import requests

class NXApi:
	PREFIX_URL = "https://nxapi-znca-api.fancy.org.uk/api/znca"
	PROJECT_URL = "https://github.com/samuelthomas2774/nxapi-znca-api"
	
	def __init__(self, user_agent, prefix_url = PREFIX_URL):
		if user_agent == None:
			print("nso-api: User Agent for iMink is not present! Please set one with a method of contact from iMink.")
			#Can throw an assert, just temporary
			sys.exit(1)

		self.debug = int(os.environ.get('NSO_API_DEBUG', 0))
		self.user_agent = user_agent
		self.prefix_url = prefix_url
		self.session = requests.Session()

	def create_f_request(self, id_token, method, nsaid):
		api_app_head = {
			'Content-Type': 'application/json; charset=utf-8',
			'User-Agent': self.user_agent,
			'x-platform' : 'Android',
			'X-znca-Version' : '2.12.0',
			'X-znca-Client-Version' : '2.12.0'
		}
		api_app_body = {
			'hash_method':  str(method),
			'token': id_token,
			'na_id': nsaid
		}

		url = self.prefix_url + "/f"
		req = requests.Request('POST', url, headers=api_app_head, data=json.dumps(api_app_body))
		return req

	def print_debug(self, req):
		if isinstance(req, requests.Request):
			print(f"{req.method} {req.url}")
		elif isinstance(req, requests.Response):
			print(f"{str(req.status_code)} {req.reason}")
		for k, v in req.headers.items():
			print(f"{k}: {v}")
		if isinstance(req, requests.Request):
			print(req.data)
		elif isinstance(req, requests.Response):
			print(req.text)

	def get_f(self, method, id_token, nsaid):
		req = self.create_f_request(id_token, method, nsaid)
		if self.debug >= 4 : self.print_debug(req)
		res = self.session.send(self.session.prepare_request(req))
		if self.debug >= 4 : self.print_debug(res)
		#print(f"nso-api: iMink: {res.text}")
		if res.status_code != 200:
			print(f'Unexpected HTTP code "{res.status_code} {res.reason}" from imink f')
			return None

		return res.json()

	def get_nso_f(self, id_token, nsaid):
		return self.get_f(1, id_token, nsaid)

	def get_app_f(self, web_api_token, nsaid):
		return self.get_f(2, web_api_token, nsaid)

	def get_supported_app_version(self):
		url = self.prefix_url + "/config"

		req = requests.Request("GET", url)
		res = self.session.send(self.session.prepare_request(req))
		if res.status_code != 200:
			print(f'Unexpected HTTP code "{res.status_code} {res.reason}" from imink config')
			return None

		config = res.json()
		ver = config.get("nso_version")
		return ver
