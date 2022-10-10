import requests
import urllib
import re

from .nso_expiring_token import NSO_Expiring_Token

class NSO_API_S3:
	def __init__(self, nso_api):
		self.nso_api = nso_api
		self.game_id = 4834290508791808  # Splatoon 3
		self.hostname = 'api.lp1.av5ja.srv.nintendo.net'
		self.web_app_version = '1.0.0-216d0219'  # TODO: Track this somehow?
		self.web_service_token = None
		self.bullet_token = None

	def get_keys(self):
		keys = {}
		keys['web_service_token'] = self.web_service_token.to_hash() if self.web_service_token else None
		keys['bullet_token'] = self.bullet_token.to_hash() if self.bullet_token else None
		return keys

	def set_keys(self, keys):
		if keys is None:
			return
		self.web_service_token = NSO_Expiring_Token.from_hash(keys['web_service_token']) if keys.get('web_service_token') else None
		self.bullet_token = NSO_Expiring_Token.from_hash(keys['bullet_token']) if keys.get('bullet_token') else None

	def get_web_app_js_url(self):
		headers = {}
		headers['Host'] = self.hostname
		headers['Accept-Language'] = 'en-US'

		# Get web app HTML
		web_app_url = f"https://{self.hostname}/"
		req = requests.Request('GET', web_app_url, headers = headers)
		html = self.nso_api.do_html_request(req)
		if html is None:
			return None

		# Find script tag
		script = html.find(lambda tag: (tag.name == 'script') and tag.has_attr('src') and re.search("/static/", tag.get('src')))
		if script is None:
			self.nso_api.errors.append("Couldn't find S3 web app script tag")
			return None

		js_url = urllib.parse.urljoin(web_app_url, script.get('src'))
		return js_url

	def get_web_app_version(self, js_url):
		headers = {}
		headers['Host'] = self.hostname
		headers['Accept-Language'] = 'en-US'

		# Get JS
		req = requests.Request('GET', js_url, headers = headers)
		res = self.nso_api.do_http_request(req)
		if res is None:
			self.nso_api.errors.append(f"Couldn't retrieve S3 web app javascript from {js_url}")
			return None

		# Yank out the version info
		js = res.text
		match = re.search('"(\\d+[.]\\d+[.]\\d+)-"[^;]+"([a-fA-F0-9]{40})', js)
		if match is None:
			self.nso_api.errors.append(f"Couldn't find version number within S3 web app javascript")
			return None

		return {"url": js_url, "version": match[1], "revision": match[2]}

	def create_bullet_token_request(self):
		if not self.web_service_token:
			raise Exception("No web_service_token")

		if not self.nso_api.user_info:
			raise Exception("No user_info")

		headers = {}
		headers['Host'] = self.hostname
		headers['User-Agent'] = f'com.nintendo.znca/{self.nso_api.app_version} (Android/7.1.2)'
		headers['Content-Type'] = 'application/json; charset=utf-8'
		headers['X-Platform'] = 'Android'
		headers['X-Web-View-Ver'] = self.web_app_version
		headers['X-NACOUNTRY'] = self.nso_api.user_info['country']
		headers['Accept-Language'] = 'en-US'
		headers['X-GameWebToken'] = self.web_service_token.value
		headers['Connection'] = 'keep-alive'

		body = ''  # NOTE: Blank body is sent even though content-type specifies JSON

		url = f"https://{self.hostname}/api/bullet_tokens"
		req = requests.Request('POST', url, headers = headers, data = body)
		return req

	def create_graphql_request(self, query_hash, variables):
		if not self.bullet_token:
			raise Exception("No bullet_token")

		headers = {}
		headers['Host'] = self.hostname
		headers['User-Agent'] = f'com.nintendo.znca/{self.nso_api.app_version} (Android/7.1.2)'
		headers['Content-Type'] = 'application/json; charset=utf-8'
		headers['X-Web-View-Ver'] = self.web_app_version
		headers['Accept-Language'] = 'en-US'
		headers['Authorization'] = f"Bearer {self.bullet_token.value}"

		jsonbody = {}
		jsonbody['variables'] = variables
		jsonbody['extensions'] = {}
		jsonbody['extensions']['persistedQuery'] = {}
		jsonbody['extensions']['persistedQuery']['version'] = 1
		jsonbody['extensions']['persistedQuery']['sha256Hash'] = query_hash

		url = f"https://{self.hostname}/api/graphql"
		req = requests.Request('POST', url, headers = headers, json = jsonbody)
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

	def ensure_bullet_token(self):
		if self.bullet_token and not self.bullet_token.is_expired():
			return True

		if not self.ensure_web_service_token():
			return False

		if not self.nso_api.ensure_user_info():
			return False

		response = self.nso_api.do_json_request(self.create_bullet_token_request(), expect_status = [201])
		if not response:
			return False

		if response.get('bulletToken') is None:
			self.nso_api.errors.append("No bulletToken in response")
			return False

		duration = 3600 * 2  # Reportedly expires after 2 hours
		bullet_token = NSO_Expiring_Token(response['bulletToken'], duration = duration)

		self.bullet_token = bullet_token
		self.nso_api.notify_keys_update()
		return True

	def do_graphql_request(self, query_hash, variables):
		if not self.ensure_bullet_token():
			return None

		response = self.nso_api.do_json_request(self.create_graphql_request(query_hash, variables))
		return response

	def get_battle_history_list(self):
		return self.do_graphql_request('7d8b560e31617e981cf7c8aa1ca13a00', {})

	def get_battle_history_detail(self, id):
		return self.do_graphql_request('2b085984f729cd51938fc069ceef784a', {'vsResultId': id});

	def get_stage_schedule(self):
		return self.do_graphql_request('7d4bb0565342b7385ceb97d109e14897', {})

	def get_player_stats_simple(self):
		return self.do_graphql_request('f8ae00773cc412a50dd41a6d9a159ddd', {})

	def get_player_stats_full(self):
		return self.do_graphql_request('29957cf5d57b893934de857317cd46d8', {})

	def get_salmon_run_stats(self):
		return self.do_graphql_request('817618ce39bcf5570f52a97d73301b30', {})

	def get_current_splatfest(self):
		return self.do_graphql_request('c0429fd738d829445e994d3370999764', {})

	def get_splatfest_list(self):
		return self.do_graphql_request('44c76790b68ca0f3da87f2a3452de986', {})

	def get_weapon_stats(self):
		return self.do_graphql_request('a0c277c719b758a926772879d8e53ef8', {})

	def get_fits(self):
		return self.do_graphql_request('81d9a6849467d2aa6b1603ebcedbddbe', {})

	def get_maps_stats(self):
		return self.do_graphql_request('56c46bdbdfa4519eaf7845ce9f3cd67a', {})

	def do_store_order(self, id, confirm=False):
		return self.do_graphql_request('b79b7a101a243912754f72437e2ad7e5', {'input' : { 'id': id, 'isForceOrder': confirm } })

	def get_store_items(self):
		return self.do_graphql_request('a43dd44899a09013bcfd29b4b13314ff', {})

	def get_single_player_stats(self):
		return self.do_graphql_request('fbee1a882371d4e3becec345636d7d1c', {})

	def get_species_cur_weapon(self):
		return self.do_graphql_request('49dd00428fb8e9b4dde62f585c8de1e0', {})

	def get_sr_history(self):
		return self.do_graphql_request('a5692cf290ffb26f14f0f7b6e5023b07', {})

	def get_sr_history_detail(self, id):
		return self.do_graphql_request('f3799a033f0a7ad4b1b396f9a3bafb1e', {'coopHistoryDetailId': id})
