import requests
import urllib
import json
import base64
import os
import hashlib
import uuid
import time

from .nso_expiring_token import NSO_Expiring_Token
from .nso_api_s2 import NSO_API_S2

class NSO_API:
	def __init__(self, app_version, f_provider, context = None):
		self.session = requests.Session()
		self.app_version = app_version
		self.f_provider = f_provider
		self.client_id = '71b963c1b7b6d119'
		self.callbacks = {}
		self.context = context
		self.login = None
		self.session_token = None
		self.api_tokens = None
		self.user_info = None
		self.last_activity_time = time.time()
		self.s2 = NSO_API_S2(self)
		self.errors = []

	def get_idle_seconds(self):
		return time.time() - self.last_activity_time

	# Returns true if "logged in". This just means the user has completed
        #  the process of getting us a session_token.
	def is_logged_in(self):
		return self.session_token != None

	def set_session_token(self, session_token):
		self.session_token = session_token

	def on_keys_update(self, callback):
		self.callbacks['keys_update'] = callback

	def notify_keys_update(self):
		if not self.callbacks.get('keys_update'):
			return
		self.callbacks['keys_update'](self, self.context)

	def get_keys(self):
		keys = {}
		keys['session_token'] = self.session_token
		keys['api_tokens'] = self.api_tokens.to_hash() if self.api_tokens else None
		keys['games'] = {}
		keys['games']['s2'] = self.s2.get_keys()
		return keys

	def set_keys(self, keys):
		self.session_token = keys.get('session_token')
		self.api_tokens = NSO_Expiring_Token.from_hash(keys['api_tokens']) if keys.get('api_tokens') else None
		if keys.get('games'):
			self.s2.set_keys(keys['games'].get('s2'))

	def get_error_message(self):
		if len(self.errors) == 0:
			return 'No error'
		msg = '; '.join(self.errors)
		self.errors = []
		return msg

	def base64_encode_no_pad(self, data):
		return base64.urlsafe_b64encode(data).replace(b"=", b"")

	def generate_login_challenge(self):
		login = {}
		login['state'] = self.base64_encode_no_pad(os.urandom(36))
		login['code_verifier'] = self.base64_encode_no_pad(os.urandom(32))
		login['code_challenge'] = self.base64_encode_no_pad(hashlib.sha256(login['code_verifier']).digest())
		return login

	# Decodes the 'npf71b963c1b7b6d119://auth#...' URL provided by Nintendo
	def decode_login_url(self, urlstring):
		url = urllib.parse.urlparse(urlstring)
		if url.scheme != ('npf' + self.client_id):
			return None
		return dict(urllib.parse.parse_qsl(url.fragment))

	# Creates a session_token request. During login, we generate the
	#  code_verifier and a special login URL. The user visits the
	#  URL and provides a resultant URL that contains the
	#  session_token_code. This request takes the session_token_code
	#  matching our login URL and gives us the a session_token.
	def create_session_token_request(self, session_token_code):
		headers = {}
		headers['User-Agent'] = f'OnlineLounge/{self.app_version} NASDKAPI Android'
		headers['Accept-Language'] = 'en-US'
		headers['Accept'] = 'application/json'
		headers['Content-Type'] = 'application/x-www-form-urlencoded'
		headers['Host'] = 'accounts.nintendo.com'
		headers['Connection'] = 'Keep-Alive'
		headers['Accept-Encoding'] = 'gzip'

		body = {}
		body['client_id'] = self.client_id
		body['session_token_code'] = session_token_code
		body['session_token_code_verifier'] = self.login['code_verifier']

		req = requests.Request('POST', 'https://accounts.nintendo.com/connect/1.0.0/api/session_token', headers=headers, data=body)
		return req

	# Creates an api_tokens request.
	# Given the session_token, we receive the api_tokens.
	def create_api_tokens_request(self):
		if not self.session_token:
			raise Exception("No session_token")

		headers = {}
		headers['Host'] = 'accounts.nintendo.com'
		headers['Accept-Encoding'] = 'gzip'
		headers['Content-Type'] = 'application/json; charset=utf-8'
		headers['Accept-Language'] = 'en-US'
		headers['Accept'] = 'application/json'
		headers['Connection'] = 'Keep-Alive'
		headers['User-Agent'] = f'OnlineLounge/{self.app_version} NASDKAPI Android'

		jsonbody = {}
		jsonbody['client_id'] = self.client_id
		jsonbody['session_token'] = self.session_token
		jsonbody['grant_type'] = 'urn:ietf:params:oauth:grant-type:jwt-bearer-session-token'

		req = requests.Request('POST', 'https://accounts.nintendo.com/connect/1.0.0/api/token', headers=headers, json=jsonbody)
		return req

	def create_user_info_request(self):
		if not self.api_tokens:
			raise Exception("No api_tokens")

		headers = {}
		headers['User-Agent'] = f'OnlineLounge/{self.app_version} NASDKAPI Android'
		headers['Accept-Language'] = 'en-US'
		headers['Accept'] = 'application/json'
		headers['Authorization'] = f"Bearer {self.api_tokens.value['access_token']}"
		headers['Host'] = 'api.accounts.nintendo.com'
		headers['Connection'] = 'Keep-Alive'
		headers['Accept-Encoding'] = 'gzip'

		req = requests.Request('GET', 'https://api.accounts.nintendo.com/2.0.0/users/me', headers=headers)
		return req

	def create_api_login_request(self, f, timestamp, guid):
		if not self.api_tokens:
			raise Exception("No api_tokens")

		if not self.user_info:
			raise Exception("No user_info")

		headers = {}
		headers['Host'] = 'api-lp1.znc.srv.nintendo.net'
		headers['Accept-Language'] = 'en-US'
		headers['User-Agent'] = f'com.nintendo.znca/{self.app_version} (Android/7.1.2)'
		headers['Accept'] = 'application/json'
		headers['X-ProductVersion'] = self.app_version
		headers['Content-Type'] = 'application/json; charset=utf-8'
		headers['Connection'] = 'Keep-Alive'
		headers['Authorization'] = 'Bearer'
		headers['X-Platform'] = 'Android'
		headers['Accept-Encoding'] = 'gzip'

		jsonbody = {}
		jsonbody['parameter'] = {}
		jsonbody['parameter']['f'] = f
		jsonbody['parameter']['naIdToken'] = self.api_tokens.value['id_token']
		jsonbody['parameter']['timestamp'] = timestamp
		jsonbody['parameter']['requestId'] = guid
		jsonbody['parameter']['naCountry'] = self.user_info['country']
		jsonbody['parameter']['naBirthday'] = self.user_info['birthday']
		jsonbody['parameter']['language'] = self.user_info['language']

		req = requests.Request('POST', 'https://api-lp1.znc.srv.nintendo.net/v3/Account/Login', headers=headers, json=jsonbody)
		return req

	def create_web_service_token_request(self, api_login, game_id, app_f, api_login_access_token, timestamp, guid):
		headers = {}
		headers['Host'] = 'api-lp1.znc.srv.nintendo.net'
		headers['User-Agent'] = f'com.nintendo.znca/{self.app_version} (Android/7.1.2)'
		headers['Accept'] = 'application/json'
		headers['X-ProductVersion'] = self.app_version
		headers['Content-Type'] = 'application/json; charset=utf-8'
		headers['Connection'] = 'Keep-Alive'
		headers['Authorization'] = f'Bearer {api_login["result"]["webApiServerCredential"]["accessToken"]}'
		headers['X-Platform'] = 'Android'
		headers['Accept-Encoding'] = 'gzip'

		jsonbody = {}
		jsonbody['parameter'] = {}
		jsonbody['parameter']['f'] = app_f
		jsonbody['parameter']['id'] = game_id
		jsonbody['parameter']['registrationToken'] = api_login_access_token
		jsonbody['parameter']['timestamp'] = timestamp
		jsonbody['parameter']['requestId'] = guid

		req = requests.Request('POST', 'https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken', headers=headers, json=jsonbody)
		return req

	# Utility method to print out a requests.Request or request.Response object.
	def dump_http_message(self, message):
		print(message)
		if isinstance(message, requests.Request) or isinstance(message, requests.PreparedRequest):
			print(message.method + " " + message.url)
		elif isinstance(message, requests.Response):
			print(str(message.status_code) + " " + message.reason)

		for k, v in message.headers.items():
			print(f"{k}: {v}")

		print()
		if isinstance(message, requests.Request) or isinstance(message, requests.PreparedRequest):
			print(message.body)
		elif isinstance(message, requests.Response):
			print(message.text)

	# Sends the given request and expects a 200 response.
	# Returns a requests.Response object.
	def do_http_request(self, req):
		self.last_activity_time = time.time()
		res = self.session.send(self.session.prepare_request(req))
		#self.dump_http_message(res.request)
		#self.dump_http_message(res)
		if res.status_code != 200:
			self.errors.append(f'Unexpected HTTP code {res.status_code} from request')
			return None
		return res

	# Sends the given request and expects JSON data in return.
	# Returns the decoded JSON payload.
	def do_json_request(self, req):
		res = self.do_http_request(req)
		return json.loads(res.text)

	def get_login_challenge_url(self):
		login = self.generate_login_challenge()

		params = {}
		params['state'] = login['state']
		params['redirect_uri'] = 'npf' + self.client_id + '://auth'
		params['client_id'] = self.client_id
		params['scope'] = 'openid user user.birthday user.mii user.screenName'
		params['response_type'] = 'session_token_code'
		params['session_token_code_challenge'] = login['code_challenge']
		params['session_token_code_challenge_method'] = 'S256'
		params['theme'] = 'login_form'

		login_url = "https://accounts.nintendo.com/connect/1.0.0/authorize?" + urllib.parse.urlencode(params)
		login[login_url] = login_url

		self.login = login

		return login_url

	# Given the post-login URL, retrieves the session_token.
	# Returns True or False according to success.
	def complete_login_challenge(self, urlstring):
		if not self.login:
			self.errors.append('No login in progress')
			return False

		fields = self.decode_login_url(urlstring)
		if not fields:
			self.errors.append('Could not decode URL')
			return False

		if not fields.get('session_token_code'):
			self.errors.append('Expected session_token_code in URL')
			return False

		result = self.do_json_request(self.create_session_token_request(fields['session_token_code']))
		if not result.get('session_token'):
			self.errors.append('session_token response returned no token')
			return False

		self.login = None  # Login complete, so delete login challenge data

		self.session_token = result['session_token']
		return True

	# Ensures we have fresh api_tokens.
	# Returns True if successful.
	def ensure_api_tokens(self):
		if self.api_tokens and self.api_tokens.is_fresh():
			return True

		result = self.do_json_request(self.create_api_tokens_request())
		if not result:
			return False

		self.api_tokens = NSO_Expiring_Token(result, duration = result['expires_in'])
		self.notify_keys_update()
		return True

	# Ensures we have user_info.
	# Returns True if successful.
	def ensure_user_info(self):
		if self.user_info:
			return True

		result = self.do_json_request(self.create_user_info_request())
		if not result:
			return False

		self.user_info = result
		return True

	# Gets the web_service_token for a specific game id.
        # Returns an NSO_Expiring_Token object on success.
	def get_web_service_token(self, game_id):
		if not self.is_logged_in():
			self.errors.append("Not logged in")
			return None

		if not self.ensure_api_tokens():
			self.errors.append("Could not get api_tokens")
			return None

		if not self.ensure_user_info():
			self.errors.append("Could not get user_info")
			return None

		timestamp = int(time.time())
		guid = str(uuid.uuid4())

		nso_f = self.f_provider.get_nso_f(self.api_tokens.value['id_token'], guid, timestamp)
		print(f"NSO f: {nso_f}")

		# TODO: Save the api_login and skip it when fresh? Could be a
                #  win if we're gathering tokens for multiple games.
		api_login = self.do_json_request(self.create_api_login_request(nso_f, timestamp, guid))
		if not api_login:
			return None
		elif api_login.get("status") != 0:
			self.errors.append("Unexpected response getting api login")
			return None

		app_f = self.f_provider.get_app_f(api_login['result']['webApiServerCredential']['accessToken'], guid, timestamp)
		print(f"App f: {app_f}")

		web_service_token = self.do_json_request(self.create_web_service_token_request(api_login, game_id, app_f, api_login['result']['webApiServerCredential']['accessToken'], timestamp, guid))
		if not web_service_token:
			return None
		elif web_service_token.get("status") != 0:
			self.errors.append("Unexpected response getting web service token")
			return None

		#print(web_service_token)
		return NSO_Expiring_Token(web_service_token['result']['accessToken'], duration = web_service_token['result']['expiresIn'])
