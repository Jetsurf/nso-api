import requests
import urllib
import json
import base64
import os
import hashlib
import uuid
import time
import inspect
import re
import bs4

import nso_api.utils

from .version import __version__

from .nso_expiring_token import NSO_Expiring_Token
from .nso_api_app import NSO_API_App
from .nso_api_s2 import NSO_API_S2
from .nso_api_s3 import NSO_API_S3
from .nso_api_acnh import NSO_API_ACNH
from .nso_api_account import NSO_API_Account

class NSO_JSON_Response:
	def __init__(self, response):
		self.response = response  # requests.Response object
		self.payload  = None      # Decoded payload
		self.decode()

	def decode(self):
		if self.response is None:
			return

		mime_type = self.response.headers['content-type']
		if (not mime_type) or (not re.match("^application/json\\b", mime_type)):
			return

		self.payload = json.loads(self.response.text)

	def is_http_error(self):
		return not ((self.response.status_code >= 200) and (self.response.status_code <= 299))

	def is_json_error(self):
		if self.payload is None:
			return False

		return self.payload.get('status') != 0

	def get_error(self):
		if self.response is None:
			return "No HTTP response"
		elif self.is_http_error():
			return f"HTTP status code {self.response.status_code}"
		elif self.is_json_error():
			return f"JSON status code {self.payload.get('status')} ({self.payload.get('errorMessage')})"

		return None

	def result(self):
		if self.payload is None:
			return None
		elif self.payload.get('status') != 0:
			return None

		return self.payload.get('result')

class NSO_API:
	FALLBACK_APP_VERSION = "2.8.1"

	DEBUG_APP_VERSION = 0x04

	global_data = {}
	global_callbacks = {}

	def __init__(self, f_provider, context = None, debug = 0):
		self.session = requests.Session()
		self.f_provider = f_provider
		self.client_id = '71b963c1b7b6d119'
		self.callbacks = {}
		self.context = context
		self.login = None
		self.session_token = None
		self.api_tokens = None
		self.api_login = None
		self.user_info = None
		self.last_activity_time = time.time()
		self.app_version_override = None
		self.cache = {}
		self.app = NSO_API_App(self)
		self.s2 = NSO_API_S2(self)
		self.s3 = NSO_API_S3(self)
		self.acnh = NSO_API_ACNH(self)
		self.account = NSO_API_Account(self)
		self.debug = max(int(os.environ.get('NSO_API_DEBUG', 0)), debug)
		self.errors = []

	@classmethod
	def get_version(cls):
		return __version__

	def debug_message(self, level, message):
		if self.debug & level:
			print(message)

	# Given an NSO_JSON_Response object, records an error message and
	#  returns True if it was an error.
	def record_response_error(self, response):
		error = None
		if not response:
			error = "No response"
		else:
			error = response.get_error()

		if not error:
			return False

		caller = inspect.stack()[1].function
		self.errors.append(f"{caller}: {error}")
		return True

	def get_idle_seconds(self):
		return time.time() - self.last_activity_time

	# Returns true if "logged in". This just means the user has completed
        #  the process of getting us a session_token.
	def is_logged_in(self):
		return self.session_token != None

	def set_session_token(self, session_token):
		self.session_token = session_token

	def on_logged_out(self, callback):
		self.callbacks['logged_out'] = callback

	def on_user_data_update(self, callback):
		self.callbacks['user_data_update'] = callback

	@classmethod
	def on_global_data_update(cls, callback):
		cls.global_callbacks['global_data_update'] = callback

	def notify_logged_out(self):
		if not self.callbacks.get('logged_out'):
			return
		self.callbacks['logged_out'](self, self.context)

	def notify_user_data_update(self):
		if not self.callbacks.get('user_data_update'):
			return
		self.callbacks['user_data_update'](self, self.context)

	@classmethod
	def notify_global_data_update(cls):
		if not cls.global_callbacks.get('global_data_update'):
			return
		cls.global_callbacks['global_data_update'](cls.global_data)

	def get_user_data(self):
		keys = {}
		keys['session_token'] = self.session_token
		keys['api_tokens'] = self.api_tokens.to_hash() if self.api_tokens else None
		keys['api_login'] = self.api_login.to_hash() if self.api_login else None
		keys['games'] = {}
		keys['games']['s2'] = self.s2.get_keys()
		keys['games']['s3'] = self.s3.get_keys()
		keys['games']['acnh'] = self.acnh.get_keys()
		return keys

	def load_user_data(self, keys):
		if not isinstance(keys, dict):
			return
		self.session_token = keys.get('session_token')
		self.api_tokens = NSO_Expiring_Token.from_hash(keys['api_tokens']) if keys.get('api_tokens') else None
		self.api_login = NSO_Expiring_Token.from_hash(keys['api_login']) if keys.get('api_login') else None
		if keys.get('games'):
			self.s2.set_keys(keys['games'].get('s2'))
			self.s3.set_keys(keys['games'].get('s3'))
			self.acnh.set_keys(keys['games'].get('acnh'))

	@classmethod
	def get_global_data(cls):
		return cls.global_data

	@classmethod
	def load_global_data(cls, data):
		if not isinstance(data, dict):
			return
		cls.global_data = data

	@classmethod
	def get_global_data_value(cls, path):
		container = cls.global_data
		parts = path.split(".")
		for p in range(len(parts) - 1):
			if not parts[p] in container:
				return None
			container = container[parts[p]]
		return container.get(parts[-1])

	@classmethod
	def set_global_data_value(cls, path, value):
		container = cls.global_data
		parts = path.split(".")
		for p in range(len(parts) - 1):
			if not parts[p] in container:
				container[parts[p]] = {}
			container = container[parts[p]]
		container[parts[-1]] = value
		cls.notify_global_data_update()

	# Discards all keys except for the session_token. This should not be
	#  needed during normal use, but can be useful for testing.
	def expire_keys(self):
		self.api_tokens = None
		self.api_login = None
		self.s2.set_keys({})
		self.s3.set_keys({})
		self.acnh.set_keys({})
		self.notify_user_data_update()
		return

	def has_error(self):
		return len(self.errors) > 0

	def get_error_message(self):
		if len(self.errors) == 0:
			return 'No error'
		msg = '; '.join(self.errors)
		self.errors = []
		return msg

	def generate_login_challenge(self):
		login = {}
		login['state'] = nso_api.utils.base64_encode_no_pad(os.urandom(36))
		login['code_verifier'] = nso_api.utils.base64_encode_no_pad(os.urandom(32))
		login['code_challenge'] = nso_api.utils.base64_encode_no_pad(hashlib.sha256(login['code_verifier']).digest())
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
		headers['User-Agent'] = f'OnlineLounge/{self.get_app_version()} NASDKAPI Android'
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
		headers['User-Agent'] = f'OnlineLounge/{self.get_app_version()} NASDKAPI Android'

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
		headers['User-Agent'] = f'OnlineLounge/{self.get_app_version()} NASDKAPI Android'
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
		headers['User-Agent'] = f'com.nintendo.znca/{self.get_app_version()} (Android/7.1.2)'
		headers['Accept'] = 'application/json'
		headers['X-ProductVersion'] = self.get_app_version()
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

	def create_web_service_token_request(self, game_id, app_f, timestamp, guid):
		if not self.api_login:
			raise Exception("No api_login")

		headers = {}
		headers['Host'] = 'api-lp1.znc.srv.nintendo.net'
		headers['User-Agent'] = f'com.nintendo.znca/{self.get_app_version()} (Android/7.1.2)'
		headers['Accept'] = 'application/json'
		headers['X-ProductVersion'] = self.get_app_version()
		headers['Content-Type'] = 'application/json; charset=utf-8'
		headers['Connection'] = 'Keep-Alive'
		headers['Authorization'] = f'Bearer {self.api_login.value}'
		headers['X-Platform'] = 'Android'
		headers['Accept-Encoding'] = 'gzip'

		jsonbody = {}
		jsonbody['parameter'] = {}
		jsonbody['parameter']['f'] = app_f
		jsonbody['parameter']['id'] = game_id
		jsonbody['parameter']['registrationToken'] = self.api_login.value
		jsonbody['parameter']['timestamp'] = timestamp
		jsonbody['parameter']['requestId'] = guid

		req = requests.Request('POST', 'https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken', headers=headers, json=jsonbody)
		return req

	def create_znc_request(self, path, params):
		if path.startswith("http:") or path.startswith("https:"):
			raise Exception("create_znc_request(): I want a path but I was given a full URL")

		if not path.startswith("/"):
			path = "/" + path

		url = "https://api-lp1.znc.srv.nintendo.net" + path

		if not self.api_login:
			raise Exception("No api_login")

		guid = str(uuid.uuid4())

		headers = {}
		headers['User-Agent'] = f'com.nintendo.znca/{self.get_app_version()} (Android/7.1.2)'
		headers['Accept-Encoding'] = 'gzip'
		headers['Accept'] = 'application/json'
		headers['Connection'] = 'Keep-Alive'
		headers['Host'] = 'api-lp1.znc.srv.nintendo.net'
		headers['X-ProductVersion'] = self.get_app_version()
		headers['Content-Type'] = 'application/json; charset=utf-8'
		headers['Authorization'] = f"Bearer {self.api_login.value}"
		headers['X-Platform'] = 'Android'

		jsonbody = {}
		jsonbody['parameter'] = params
		jsonbody['requestId'] = guid

		req = requests.Request('POST', url, headers = headers, json = jsonbody)
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

	# Sends the given request and expects a 2xx response.
	# Returns a requests.Response object.
	def do_http_request(self, req, expect_status = None):
		if not expect_status:
			expect_status = [200]

		prep_req = self.session.prepare_request(req)

		if self.debug & 0x02:
			self.dump_http_message(prep_req)
		elif self.debug & 0x01:
			print(f">> {prep_req.method} {prep_req.url}")

		self.last_activity_time = time.time()
		res = self.session.send(prep_req)

		if self.debug & 0x02:
			self.dump_http_message(res)
		elif self.debug & 0x01:
			print(f"<< {res.status_code} {res.reason}")

		if not res.status_code in expect_status:
			self.errors.append(f'Unexpected HTTP code {res.status_code} from request, wanted {expect_status}')
			return None
		return res

	# Sends the given request and expects JSON data in return.
	# Returns the decoded JSON payload.
	def do_json_request(self, req, expect_status = None):
		res = self.do_http_request(req, expect_status = expect_status)
		if res == None:
			return None
		return json.loads(res.text)

	# Sends the given request and expects HTML data in return.
	# Returns a BeautifulSoup object.
	def do_html_request(self, req, expect_status = None):
		res = self.do_http_request(req, expect_status = expect_status)
		if res == None:
			return None

		mimetype = res.headers.get('Content-Type')
		if not re.match('^text/x?html\\b', mimetype):
			self.errors.append(f'Unexpected HTTP Content-Type \'{mimetype}\', wanted text/html')
			return None

		return bs4.BeautifulSoup(res.text, 'html5lib')

	# Performs an authenticated call to api-lp1.znc.srv.nintendo.net.
	def do_znc_call(self, path, params):
		if not self.ensure_api_login():
			return None

		request = self.create_znc_request(path, params)
		#result = self.do_json_request(request)
		response = self.do_http_request(request)
		return NSO_JSON_Response(response)

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

		if not self.ensure_app_version():
			return False

		result = self.do_json_request(self.create_session_token_request(fields['session_token_code']))
		if not result.get('session_token'):
			self.errors.append('session_token response returned no token')
			return False

		self.login = None  # Login complete, so delete login challenge data

		self.session_token = result['session_token']
		self.notify_user_data_update()
		return True

	# Override the app_version to a specific version number
	def override_app_version(self, version):
		self.app_version_override = version

	# Ensures we have a Nintendo app version.
	def ensure_app_version(self):
		if self.app_version_override is not None:
			self.debug_message(self.DEBUG_APP_VERSION, f"App version: Overridden to: {repr(self.app_version_override)}")
			return True

		app_version = self.get_global_data_value("app_version")
		if app_version is not None:
			self.debug_message(self.DEBUG_APP_VERSION, f"App version: Cached data: {repr(app_version)}")
			if time.time() < app_version['expiretime']:
				self.debug_message(self.DEBUG_APP_VERSION, f"App version: Cached version still fresh.")
				return True

		self.debug_message(self.DEBUG_APP_VERSION, "App version: Cached version out of date...")

		if hasattr(self.f_provider, "get_supported_app_version") and callable(self.f_provider.get_supported_app_version):
			self.debug_message(self.DEBUG_APP_VERSION, "App version: F provider supports app versions, checking...")
			version = self.f_provider.get_supported_app_version()
			if version and re.match(r'^\d+\.\d+\.\d+$', version):
				now = int(time.time())
				expiretime = now + (24 * 3600)
				self.set_global_data_value("app_version", {"retrievetime": now, "expiretime": expiretime, "data": {"version": version}})
				self.debug_message(self.DEBUG_APP_VERSION, f"App version: F provider reported version '{version}'...")
				return True

		self.debug_message(self.DEBUG_APP_VERSION, "App version: Checking app store")
		version = self.app.get_version()
		if version is None:
			self.debug_message(self.DEBUG_APP_VERSION, f"  Failed to get app version, using fallback version {self.FALLBACK_APP_VERSION}")
			now = int(time.time())
			expiretime = now + 3600
			self.set_global_data_value("app_version", {"retrievetime": now, "expiretime": expiretime, "data": {"version": self.FALLBACK_APP_VERSION, "fallback": True}})
			return False

		self.debug_message(self.DEBUG_APP_VERSION, f"  Found app version: {version}")

		now = int(time.time())
		expiretime = now + (24 * 3600)
		self.set_global_data_value("app_version", {"retrievetime": now, "expiretime": expiretime, "data": {"version": version}})
		return True

	def get_app_version(self):
		if self.app_version_override is not None:
			self.debug_message(self.DEBUG_APP_VERSION, f"App version: Using override version '{self.app_version_override}'")
			return self.app_version_override

		app_version = self.get_global_data_value("app_version")
		if app_version is not None:
			self.debug_message(self.DEBUG_APP_VERSION, f"App version: Using cached version '{app_version['data']['version']}'")
			return app_version['data']['version']

		self.debug_message(self.DEBUG_APP_VERSION, f"App version: Using fallback version '{self.FALLBACK_APP_VERSION}'")
		return self.FALLBACK_APP_VERSION

	# Ensures we have fresh api_tokens.
	# Returns True if successful.
	def ensure_api_tokens(self):
		if self.api_tokens and self.api_tokens.is_fresh():
			return True

		if not self.ensure_app_version():
			return False

		response = self.do_http_request(self.create_api_tokens_request(), expect_status = [200, 400])
		if response is None:
			self.errors.append("Request for api_tokens failed")
			return False
		if response.status_code != 200:
			result = None
			try:
				result = json.loads(response.text)
			except:
				pass

			if result and result.get('error') and (result.get('error') == 'invalid_grant'):
				self.errors.append(f"Client is logged out")
				self.notify_logged_out()
				self.session_token = None
				self.notify_user_data_update()
				return False

			self.errors.append(f"Request for api_tokens gave status code {response.status_code}")
			return False

		result = json.loads(response.text)

		self.api_tokens = NSO_Expiring_Token(result, duration = result['expires_in'])
		self.notify_user_data_update()
		return True

	# Ensures we have user_info.
	# Returns True if successful.
	def ensure_user_info(self):
		if self.user_info:
			return True

		if not self.ensure_api_tokens():
			return False

		result = self.do_json_request(self.create_user_info_request())
		if not result:
			self.errors.append("Request for user_info failed")
			return False

		self.user_info = result
		return True

	def ensure_api_login(self):
		if self.api_login and self.api_login.is_fresh():
			return True

		if not self.ensure_user_info():
			return False

		if not self.is_logged_in():
			self.errors.append("Not logged in")
			return False

		if not self.ensure_api_tokens():
			self.errors.append("Could not get api_tokens")
			return False

		guid = str(uuid.uuid4())
		nso_f_dict = self.f_provider.get_nso_f(self.api_tokens.value['id_token'], guid, self.user_info['id'])
		if not nso_f_dict:
			self.errors.append("Could not get nso f hash from f_provider")
			return False

		api_login_response = self.do_json_request(self.create_api_login_request(nso_f_dict['f'], nso_f_dict['timestamp'], guid))
		if not api_login_response:
			self.errors.append("API login request failed")
			return False
		elif api_login_response.get("status") != 0:
			self.errors.append("Unexpected response getting api login")
			return False

		# Cache the user's friend code
		self.cache['friend_code'] = api_login_response['result']['user']['links']['friendCode']['id']

		wasc = api_login_response['result']['webApiServerCredential']
		self.api_login = NSO_Expiring_Token(wasc['accessToken'], duration = wasc['expiresIn'])
		self.notify_user_data_update()
		return True

	# Gets the web_service_token for a specific game id.
	# Returns an NSO_Expiring_Token object on success.
	def get_web_service_token(self, game_id):
		if not self.ensure_api_login():
			return None

		if not self.ensure_app_version():
			return False

		if not self.ensure_user_info():
			return False

		guid = str(uuid.uuid4())
		app_f_dict = self.f_provider.get_app_f(self.api_login.value, guid, self.user_info['id'])
		if not app_f_dict:
			self.errors.append("Could not get app f hash from f_provider")
			return False

		web_service_token_response = self.do_json_request(self.create_web_service_token_request(game_id, app_f_dict['f'], app_f_dict['timestamp'], guid))
		if not web_service_token_response:
			return None
		elif web_service_token_response.get("status") != 0:
			self.errors.append("Unexpected response getting web service token")
			return None

		return NSO_Expiring_Token(web_service_token_response['result']['accessToken'], duration = web_service_token_response['result']['expiresIn'])

	# Returns friend code if known.
	def get_cached_friend_code(self):
		return self.cache.get("friend_code")
