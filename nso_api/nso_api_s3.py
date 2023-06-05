import requests
import urllib
import base64
import re
import time
import hashlib

from .nso_expiring_token import NSO_Expiring_Token
import nso_api.utils

class NSO_API_S3:
	FALLBACK_VERSION = {"version": "4.0.0", "revision": "d51784409653a32bc05fe77704381de83c61fbb2"}

	GRAPHQL_QUERY_IDS = {
		'BankaraBattleHistoriesQuery':                            '0438ea6978ae8bd77c5d1250f4f84803',
		'BankaraBattleHistoriesRefetchQuery':                     '92b56403c0d9b1e63566ec98fef52eb3',
		'BattleHistoryCurrentPlayerQuery':                        '49dd00428fb8e9b4dde62f585c8de1e0',
		'CatalogQuery':                                           'ff12098bad4989a813201b00ff22ac4e',
		'CatalogRefetchQuery':                                    '60a6592c6ee8e47245020ae0d314d378',
		'ChallengeQuery':                                         '8a079214500148bf88a8fce1d7209b90',
		'ChallengeRefetchQuery':                                  '34aedc79f96b8613501bba465295f779',
		'CheckinQuery':                                           '5d0d1b45ebf4e324d0dae017d9df06d2',
		'CheckinWithQRCodeMutation':                              'daffd9621680664dbf19d27e87484ac7',
		'ConfigureAnalyticsQuery':                                'f8ae00773cc412a50dd41a6d9a159ddd',
		'CoopHistoryDetailQuery':                                 '379f0d9b78b531be53044bcac031b34b',
		'CoopHistoryDetailRefetchQuery':                          'd3188df2fd4436870936b109675e2849',
		'CoopHistoryQuery':                                       '91b917becd2fa415890f5b47e15ffb15',
		'CoopPagerLatestCoopQuery':                               'eb947416660e0a7520549f6b9a8ffcd7',
		'CoopRecordBigRunRecordContainerPaginationQuery':         '2b83817b6e88b202d25939fe04658d33',
		'CoopRecordQuery':                                        'b2f05c682ed2aeb669a86a3265ceb713',
		'CoopRecordRefetchQuery':                                 '15035e6c4308b32d1a77e87398be5cd4',
		'CreateMyOutfitMutation':                                 '31ff008ea218ffbe11d958a52c6f959f',
		'DetailFestRecordDetailQuery':                            '96c3a7fd484b8d3be08e0a3c99eb2a3d',
		'DetailFestRefethQuery':                                  '18c7c465b18de5829347b7a7f1e571a1',
		'DetailFestVotingStatusRefethQuery':                      '92f51ed1ab462bbf1ab64cad49d36f79',
		'DetailRankingQuery':                                     'cc38f388c51f9930bd7cca966893f1b4',
		'DetailTabViewWeaponTopsArRefetchQuery':                  'a6782a0c692e8076656f9b4ab613fd82',
		'DetailTabViewWeaponTopsClRefetchQuery':                  '8d3c5bb2e82d6eb32a37eefb0e1f8f69',
		'DetailTabViewWeaponTopsGlRefetchQuery':                  'b23468857c049c2f0684797e45fabac1',
		'DetailTabViewWeaponTopsLfRefetchQuery':                  'd46f88c2ea5c4daeb5fe9d5813d07a99',
		'DetailTabViewXRankingArRefetchQuery':                    '6de3895bd90b5fa5220b5e9355981e16',
		'DetailTabViewXRankingClRefetchQuery':                    '3ab25d7f475cb3d5daf16f835a23411b',
		'DetailTabViewXRankingGlRefetchQuery':                    'd62ec65b297968b659103d8dc95d014d',
		'DetailTabViewXRankingLfRefetchQuery':                    'd96057b8f46e5f7f213a35c8ea2b8fdc',
		'DetailVotingStatusQuery':                                '53ee6b6e2acc3859bf42454266d671fc',
		'DownloadSearchReplayQuery':                              'd1841381ec4972f1bfc4742d162de0b3',
		'EventBattleHistoriesQuery':                              '9744fcf676441873c7c8a51285b6aa4d',
		'EventBattleHistoriesRefetchQuery':                       '8083b0c7f34a4bd0ef4a06ff86fc3e18',
		'EventMatchRankingPeriodQuery':                           'cdf4ffe56864817014e59c569ec8630f',
		'EventMatchRankingQuery':                                 '2acc36b477328ebb281fa91a07110e2d',
		'EventMatchRankingRefetchQuery':                          '3cfc123fe1add3c924518c1550b2936c',
		'EventMatchRankingSeasonRefetchQuery':                    'e39d7ce9875a9d6940b4b449ed5b358b',
		'FestRecordQuery':                                        '44c76790b68ca0f3da87f2a3452de986',
		'FestRecordRefetchQuery':                                 '73b9837d0e4dd29bfa2f1a7d7ee0814a',
		'FriendListQuery':                                        'f0a8ebc384cf5fbac01e8085fbd7c898',
		'FriendListRefetchQuery':                                 'aa2c979ad21a1100170ddf6afea3e2db',
		'GesotownQuery':                                          'a43dd44899a09013bcfd29b4b13314ff',
		'GesotownRefetchQuery':                                   '951cab295eafdbeccfc2e718d7a98646',
		'HeroHistoryQuery':                                       'fbee1a882371d4e3becec345636d7d1c',
		'HeroHistoryRefetchQuery':                                '4f9ae2b8f1d209a5f20302111b28f975',
		'HistoryRecordQuery':                                     'd9246baf077b2a29b5f7aac321810a77',
		'HistoryRecordRefetchQuery':                              '67921048c4af8e2b201a12f13ad0ddae',
		'HomeQuery':                                              '7dcc64ea27a08e70919893a0d3f70871',
		'JourneyChallengeDetailQuery':                            '5a199948d059985bd758cc0175131f4a',
		'JourneyChallengeDetailRefetchQuery':                     'e7414c7a64bf80bb50ce21d5ccfde772',
		'JourneyQuery':                                           'bc71fc0264f3f72256724b069f7a4097',
		'JourneyRefetchQuery':                                    '09eee118fa16415d6bc3846bc6e5d8e5',
		'LatestBattleHistoriesQuery':                             '0d90c7576f1916469b2ae69f64292c02',
		'LatestBattleHistoriesRefetchQuery':                      '6b74405ca9b43ee77eb8c327c3c1a317',
		'MyOutfitDetailQuery':                                    'd935d9e9ba7a5b6b5d6ece7f253304fc',
		'MyOutfitsQuery':                                         '81d9a6849467d2aa6b1603ebcedbddbe',
		'MyOutfitsRefetchQuery':                                  '10db4e349f3123c56df14e3adec2ee6f',
		'PagerLatestVsDetailQuery':                               '0329c535a32f914fd44251be1f489e24',
		'PagerUpdateBattleHistoriesByVsModeQuery':                'eef75ef7ce1964dfe9006bf5facde61e',
		'PhotoAlbumQuery':                                        '7e950e4f69a5f50013bba8a8fb6a3807',
		'PhotoAlbumRefetchQuery':                                 '53fb0ad32c13dd9a6e617b1158cc2d41',
		'PrivateBattleHistoriesQuery':                            '8e5ae78b194264a6c230e262d069bd28',
		'PrivateBattleHistoriesRefetchQuery':                     '89bc61012dcf170d9253f406ebebee67',
		'RankingHoldersFestTeamRankingHoldersPaginationQuery':    'f488fccdad37b9e19aed50a8d6e83a24',
		'RegularBattleHistoriesQuery':                            '3baef04b095ad8975ea679d722bc17de',
		'RegularBattleHistoriesRefetchQuery':                     '4c95233c8d55e7c8cc23aae06109a2e8',
		'ReplayModalReserveReplayDownloadMutation':               '87bff2b854168b496c2da8c0e7f3e5bc',
		'ReplayQuery':                                            'c8d9828642f6eac6894876026d3db450',
		'ReplayUploadedReplayListRefetchQuery':                   '4e83edd3d0964716c6ab27b9d6acf17f',
		'SaleGearDetailOrderGesotownGearMutation':                'b79b7a101a243912754f72437e2ad7e5',
		'SaleGearDetailQuery':                                    '6eb1b255b2cf04c08041567148c883ad',
		'SettingQuery':                                           '73bd677ed986ad2cb7004ceabfff4d38',
		'StageRecordQuery':                                       'f08a932d533845dde86e674e03bbb7d3',
		'StageRecordsRefetchQuery':                               '2fb1b3fa2d40c9b5953ea1ae263e54c1',
		'StageScheduleQuery':                                     'd1f062c14f74f758658b2703a5799002',
		'SupportButton_SupportChallengeMutation':                 '991bace9e8c52d63084cd1570a97a5b4',
		'UpdateMyOutfitMutation':                                 'bb809066282e7d659d3b9e9d4e46b43b',
		'VotesUpdateFestVoteMutation':                            'a2c742c840718f37488e0394cd6e1e08',
		'VsHistoryDetailPagerRefetchQuery':                       '994cf141e55213e6923426caf37a1934',
		'VsHistoryDetailQuery':                                   '9ee0099fbe3d8db2a838a75cf42856dd',
		'WeaponRecordQuery':                                      '5f279779e7081f2d14ae1ddca0db2b6e',
		'WeaponRecordsRefetchQuery':                              '6961f618fcef440c81509b205465eeec',
		'XBattleHistoriesQuery':                                  '6796e3cd5dc3ebd51864dc709d899fc5',
		'XBattleHistoriesRefetchQuery':                           '94711fc9f95dd78fc640909f02d09215',
		'XRankingDetailQuery':                                    'd5e4924c05891208466fcba260d682e7',
		'XRankingDetailRefetchQuery':                             'fb960404299958248b3c0a2fbb444c35',
		'XRankingQuery':                                          'd771444f2584d938db8d10055599011d',
		'XRankingRefetchQuery':                                   '5149402597bd2531b4eea04692d8bfd5',
		'myOutfitCommonDataEquipmentsQuery':                      'd29cd0c2b5e6bac90dd5b817914832f8',
		'myOutfitCommonDataFilteringConditionQuery':              'd02ab22c9dccc440076055c8baa0fa7a',
		'refetchableCoopHistory_coopResultQuery':                 '50be9b694c7c6b99b7a383e494ec5258',
		'useCurrentFestQuery':                                    'c0429fd738d829445e994d3370999764',
		'useShareMyOutfitQuery':                                  '3ba5572efce5bebbd859fc2d269d223c',
	}

	shared_cache = {}  # Cached in memory for process lifetime only

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
		now = int(time.time())
		self.shared_cache[cache_key] = {"retrievetime": now, "expiretime": now + (6 * 3600), "data": {"url": url, "text": res.text}}
		return True

	def ensure_web_app_urls(self):
		web_app_urls = self.nso_api.get_global_data_value("s3.web_app_urls")
		if web_app_urls is not None:
			if time.time() < web_app_urls['expiretime']:
				return True

		urls = self.get_web_app_urls()
		if urls is None:
			return False

		now = int(time.time())
		self.nso_api.set_global_data_value("s3.web_app_urls", {"retrievetime": now, "expiretime": now + (6 * 3600), "data": urls})
		return True

	def ensure_web_app_js(self):
		if 'web_app_js' in self.shared_cache:
			if time.time() < self.shared_cache['web_app_js']['expiretime']:
				return True

		if not self.ensure_web_app_urls():
			return False

		web_app_urls = self.nso_api.get_global_data_value("s3.web_app_urls")

		return self.cache_web_app_resource('web_app_js', web_app_urls['data']['js'])

	def ensure_web_app_css(self, css_url = None):
		if 'web_app_css' in self.shared_cache:
			if time.time() < self.shared_cache['web_app_css']['expiretime']:
				return True

		if not self.ensure_web_app_urls():
			return False

		web_app_urls = self.nso_api.get_global_data_value("s3.web_app_urls")

		return self.cache_web_app_resource('web_app_css', web_app_urls['data']['css'])

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
		now = int(time.time())
		expiretime = self.shared_cache['web_app_js']['expiretime']
		data = {"url": self.shared_cache['web_app_js']['data']['url'], "version": match[4], "revision": match[2]}
		self.nso_api.set_global_data_value("s3.web_app_version", {"retrievetime": now, "expiretime": expiretime, "data": data})
		return True

	# If we can't obtain the web app version automatically, as a fallback we can use the last-known version
	def cache_web_app_fallback_version(self):
		now = int(time.time())
		expiretime = now + (30 * 60)  # 30 minutes
		data = {"version": self.FALLBACK_VERSION['version'], "revision": self.FALLBACK_VERSION['revision'], "fallback": True}
		self.nso_api.set_global_data_value("s3.web_app_version", {"retrievetime": now, "expiretime": expiretime, "data": data})

	def ensure_web_app_version(self):
		web_app_version = self.nso_api.get_global_data_value("s3.web_app_version")
		if web_app_version is not None:
			if time.time() < web_app_version['expiretime']:
				return True

		return self.cache_web_app_version()

	def get_web_app_version(self):
		self.ensure_web_app_version()
		web_app_version = self.nso_api.get_global_data_value("s3.web_app_version")
		return web_app_version['data']

	def get_web_app_version_string(self):
		self.ensure_web_app_version()
		web_app_version = self.nso_api.get_global_data_value("s3.web_app_version")
		return f"{web_app_version['data']['version']}-{web_app_version['data']['revision'][0:8]}"

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
		headers['User-Agent'] = f'com.nintendo.znca/{self.nso_api.get_app_version()} (Android/7.1.2)'
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
		headers['User-Agent'] = f'com.nintendo.znca/{self.nso_api.get_app_version()} (Android/7.1.2)'
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
		self.nso_api.notify_user_data_update()
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
		self.nso_api.notify_user_data_update()
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

	def get_tw_history_list(self):
		return self.do_graphql_request('RegularBattleHistoriesQuery', {})

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

