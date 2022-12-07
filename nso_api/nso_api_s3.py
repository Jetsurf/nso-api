import requests
import urllib
import base64
import re
import time
import hashlib

from .nso_expiring_token import NSO_Expiring_Token
import nso_api.utils

class NSO_API_S3:
	FALLBACK_VERSION = {"version": "2.0.0", "revision": "8a061f6c34f6149b4775a13262f9e059fda92a31"}

	GRAPHQL_QUERY_IDS = {
		'LatestBattleHistoriesQuery':              '4f5f26e64bca394b45345a65a2f383bd',
		'VsHistoryDetailQuery':                    '291295ad311b99a6288fc95a5c4cb2d2',
		'StageScheduleQuery':                      '730cd98e84f1030d3e9ac86b6f1aae13',
		'ReplayQuery':                             '412b09ef4eb7b67c86333f70a40ff6ba',
		'CoopHistoryDetailQuery':                  '3cc5f826a6646b85f3ae45db51bd0707',
		'refetchableCoopHistory_coopResultQuery':  'd82a506052aef380e584c695e105f78b',
		'StageRecordQuery':                        'f08a932d533845dde86e674e03bbb7d3',
		'WeaponRecordQuery':                       '5f279779e7081f2d14ae1ddca0db2b6e',
		'CoopHistoryQuery':                        '6ed02537e4a65bbb5e7f4f23092f6154',
		'HistoryRecordQuery':                      '32b6771f94083d8f04848109b7300af5',
		'ConfigureAnalyticsQuery':                 'f8ae00773cc412a50dd41a6d9a159ddd',
		'MyOutfitsQuery':                          '81d9a6849467d2aa6b1603ebcedbddbe',
		'BattleHistoryCurrentPlayerQuery':         '49dd00428fb8e9b4dde62f585c8de1e0',
		'HeroHistoryQuery':                        'fbee1a882371d4e3becec345636d7d1c',
		'myOutfitCommonDataEquipmentsQuery':       'd29cd0c2b5e6bac90dd5b817914832f8',
		'GesotownQuery':                           'a43dd44899a09013bcfd29b4b13314ff',
		'SaleGearDetailOrderGesotownGearMutation': 'b79b7a101a243912754f72437e2ad7e5',
		'MyOutfitsQuery':                          '81d9a6849467d2aa6b1603ebcedbddbe',
		'FestRecordQuery':                         '44c76790b68ca0f3da87f2a3452de986',
		'useCurrentFestQuery':                     'c0429fd738d829445e994d3370999764',
	}

	shared_cache = {}

	def __init__(self, nso_api):
		self.nso_api = nso_api
		self.game_id = 4834290508791808  # Splatoon 3
		self.hostname = 'api.lp1.av5ja.srv.nintendo.net'
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

	def get_web_app_urls(self):
		headers = {}
		headers['Host'] = self.hostname
		headers['Accept-Language'] = 'en-US'

		# Get web app HTML
		web_app_url = f"https://{self.hostname}/"
		req = requests.Request('GET', web_app_url, headers = headers)
		html = self.nso_api.do_html_request(req)
		if html is None:
			return None

		# Find script tag for JS
		script = html.find(lambda tag: (tag.name == 'script') and tag.has_attr('src') and re.search("/static/", tag.get('src')))
		if script is None:
			self.nso_api.errors.append("Couldn't find S3 web app script tag")
			return None

		# Find link tag for CSS
		link = html.find(lambda tag: (tag.name == 'link') and tag.has_attr('href') and re.search(r'/static/', tag.get('href')) and ("stylesheet" in tag.get('rel')))
		if link is None:
			self.nso_api.errors.append("Couldn't find S3 web app link tag")
			return None

		js_url = urllib.parse.urljoin(web_app_url, script.get('src'))
		css_url = urllib.parse.urljoin(web_app_url, link.get('href'))
		return {"js": js_url, "css": css_url}

	def cache_web_app_resource(self, cache_key, url = None):
		headers = {}
		headers['Host'] = self.hostname
		headers['Accept-Language'] = 'en-US'

		# Get resource
		req = requests.Request('GET', url, headers = headers)
		res = self.nso_api.do_http_request(req)
		if res is None:
			self.nso_api.errors.append(f"Couldn't retrieve S3 web app javascript from {js_url}")
			return False

		# Save to shared cache
		now = time.time()
		self.shared_cache[cache_key] = {"retrievetime": now, "expiretime": now + (6 * 3600), "data": {"url": url, "text": res.text}}
		return True

	def ensure_web_app_urls(self):
		if 'web_app_urls' in self.shared_cache:
			if time.time() < self.shared_cache['web_app_urls']['expiretime']:
				return True

		urls = self.get_web_app_urls()
		if urls is None:
			return False

		now = int(time.time())
		self.shared_cache['web_app_urls'] = {"retrievetime": now, "expiretime": now + (6 * 3600), "urls": urls}
		return True

	def ensure_web_app_js(self):
		if 'web_app_js' in self.shared_cache:
			if time.time() < self.shared_cache['web_app_js']['expiretime']:
				return True

		if not self.ensure_web_app_urls():
			return False

		return self.cache_web_app_resource('web_app_js', self.shared_cache['web_app_urls']['urls']['js'])

	def ensure_web_app_css(self, css_url = None):
		if 'web_app_css' in self.shared_cache:
			if time.time() < self.shared_cache['web_app_css']['expiretime']:
				return True

		if not self.ensure_web_app_urls():
			return False

		return self.cache_web_app_resource('web_app_css', self.shared_cache['web_app_urls']['urls']['css'])

	def cache_web_app_version(self):
		if not self.ensure_web_app_js():
			self.cache_web_app_fallback_version()
			return False  # Couldn't get JS

		# Yank out the version info
		js = self.shared_cache['web_app_js']['data']['text']
		match = re.search(r'(["\'])([a-fA-F0-9]{40})\1.{1,96}substring\(0,8\).{1,96}(["\'`])(\d+[.]\d+[.]\d+)-', js)
		if match is None:
			self.cache_web_app_fallback_version()
			self.nso_api.errors.append(f"Couldn't find version number within S3 web app JS, using fallback version")
			return False

		# Save to shared cache
		now = time.time()
		self.shared_cache['web_app_version'] =  {"retrievetime": now, "expiretime": self.shared_cache['web_app_js']['expiretime'], "data": {"url": self.shared_cache['web_app_js']['data']['url'], "version": match[4], "revision": match[2]}}
		return True

	# If we can't obtain the web app version automatically, as a fallback we can use the last-known version
	def cache_web_app_fallback_version(self):
		now = time.time()
		expiretime = now + (30 * 60)  # 30 minutes
		self.shared_cache['web_app_version'] = {"retrievetime": now, "expiretime": expiretime, "data": {"version": self.FALLBACK_VERSION['version'], "revision": self.FALLBACK_VERSION['revision'], "fallback": True}}

	def ensure_web_app_version(self):
		if 'web_app_version' in self.shared_cache:
			if time.time() < self.shared_cache['web_app_version']['expiretime']:
				return True

		return self.cache_web_app_version()

	def get_web_app_version(self):
		self.ensure_web_app_version()
		return self.shared_cache['web_app_version']['data']

	def get_web_app_version_string(self):
		self.ensure_web_app_version()

		return f"{self.shared_cache['web_app_version']['data']['version']}-{self.shared_cache['web_app_version']['data']['revision'][0:8]}"

	def get_web_app_image_links(self):
		if not self.ensure_web_app_js():
			return None  # Couldn't get JS

		links = []
		js = self.shared_cache['web_app_js']['data']['text']
		matches = re.findall(r'"(static/media/([-_.a-zA-Z0-9]+\.(?:png|svg)))', js)
		for m in matches:
			url = urllib.parse.urljoin(f"https://{self.hostname}/", m[0])
			links.append({"url": url, "filename": m[1]})

		return links

	def extract_web_app_embedded_images(self):
		if not self.ensure_web_app_js():
			return None  # Couldn't get JS

		if not self.ensure_web_app_css():
			return None  # Couldn't get CSS

		images = {}

		for resource in ['web_app_js', 'web_app_css']:
			if not self.shared_cache[resource]:
				continue

			text = self.shared_cache[resource]['data']['text']
			matches = re.findall(r'data:(image/(?:png|jpeg|svg\+xml));base64,([A-Za-z0-9/+]+={0,2})', text)
			for m in matches:
				mimetype = m[0]
				data = base64.b64decode(m[1])
				sha256 = hashlib.sha256(data).hexdigest()
				images[sha256] = {"mimetype": mimetype, "sha256": sha256, "data": data}

		return list(images.values())

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
		headers['X-Web-View-Ver'] = self.get_web_app_version_string()
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
		headers['X-Web-View-Ver'] = self.get_web_app_version_string()
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

	def do_graphql_request(self, query, variables):
		if not self.ensure_bullet_token():
			return None

		# The query can be specified either by name or as a 32-character hex string.
		query_hash = self.GRAPHQL_QUERY_IDS.get(query)
		if (query_hash is None) and (len(query) == 32) and re.match(r'^[0-9a-f]{32}$', query):
			query_hash = query
		elif query_hash is None:
			raise Exception("Unknown query")

		response = self.nso_api.do_json_request(self.create_graphql_request(query_hash, variables))
		return response

	def get_battle_history_list(self):
		return self.do_graphql_request('LatestBattleHistoriesQuery', {})

	def get_battle_history_detail(self, id):
		return self.do_graphql_request('VsHistoryDetailQuery', {'vsResultId': id});

	def get_stage_schedule(self):
		return self.do_graphql_request('StageScheduleQuery', {})

	def get_player_stats_simple(self):
		return self.do_graphql_request('ConfigureAnalyticsQuery', {})

	def get_player_stats_full(self):
		return self.do_graphql_request('HistoryRecordQuery', {})

	def get_salmon_run_stats(self):
		return self.do_graphql_request('CoopHistoryQuery', {})

	def get_current_splatfest(self):
		return self.do_graphql_request('useCurrentFestQuery', {})

	def get_splatfest_list(self):
		return self.do_graphql_request('FestRecordQuery', {})

	def get_weapon_stats(self):
		return self.do_graphql_request('WeaponRecordQuery', {})

	def get_fits(self):
		return self.do_graphql_request('MyOutfitsQuery', {})

	def get_maps_stats(self):
		return self.do_graphql_request('StageRecordQuery', {})

	def do_store_order(self, id, confirm=False):
		return self.do_graphql_request('SaleGearDetailOrderGesotownGearMutation', {'input' : { 'id': id, 'isForceOrder': confirm } })

	def get_store_items(self):
		return self.do_graphql_request('GesotownQuery', {})

	def get_single_player_stats(self):
		return self.do_graphql_request('HeroHistoryQuery', {})

	def get_species_cur_weapon(self):
		return self.do_graphql_request('BattleHistoryCurrentPlayerQuery', {})

	def get_sr_history_list(self):
		return self.do_graphql_request('refetchableCoopHistory_coopResultQuery', {})

	def get_sr_history_detail(self, id):
		return self.do_graphql_request('CoopHistoryDetailQuery', {'coopHistoryDetailId': id})

	def get_outfits(self):
		return self.do_graphql_request('MyOutfitsQuery', {})

	def get_outfits_common_data(self):
		return self.do_graphql_request('myOutfitCommonDataEquipmentsQuery', {})

	def get_replay_list(self):
		return self.do_graphql_request('ReplayQuery', {})

	# Used to collect data for LeanYoshi's gear seed checker at https://leanny.github.io/splat3seedchecker/.
	def get_gear_seed_data(self):
		# Get outfits data
		if not (outfits_data := self.get_outfits_common_data()):
			print("Couldn't get outfits data")
			return None

		# Get battle history list
		if not (history_list := self.get_battle_history_list()):
			print("Couldn't get battle history list")
			return None

		# Extract base64 player id string
		b64_player_id = None
		if len(groups := history_list['data']['latestBattleHistories']['historyGroupsOnlyFirst']['nodes']) and len(groups[0]['historyDetails']['nodes']):
			b64_player_id = groups[0]['historyDetails']['nodes'][0]['player']['id']

		if b64_player_id is None:
			print("Couldn't find player_id")
			return None

		# Extract raw player id
		player_id = base64.b64decode(b64_player_id).decode("utf-8")
		if not (match := re.search(r':(u-[a-z0-9]{20})$', player_id)):
			print("Couldn't extract raw player id")
			return None

		# Generate a hash of the raw player id (including "u-" prefix)
		raw_player_id = match[1].encode("utf-8")
		hash = nso_api.utils.murmurhash3_32(raw_player_id, 0)

		# Create a "key" (obfuscated user id) by xoring the low byte
		#  of the hash with each byte of the raw player id
		key = bytes([(b ^ (hash & 0xFF)) for b in list(raw_player_id)])

		data = {}
		data['h'] = hash
		data['key'] = base64.b64encode(key).decode("utf-8")
		data['timestamp'] = int(time.time())
		data['gear'] = outfits_data
		return data

