import requests
import urllib
import base64
import re
import time
import hashlib

from .nso_expiring_token import NSO_Expiring_Token
import nso_api.utils

class NSO_API_S3:
	FALLBACK_VERSION = {"version": "4.0.0", "revision": "091d428399dc86fd3a7fc43d64bd33b8bd1e875d"}

	GRAPHQL_QUERY_IDS = {
		'BankaraBattleHistoriesQuery':                            '9863ea4744730743268e2940396e21b891104ed40e2286789f05100b45a0b0fd',
		'BankaraBattleHistoriesRefetchQuery':                     '7673fe37d5d5d81fa37d0b1cc02cffd7453a809ecc76b000c67d61aa51a39890',
		'BattleHistoryCurrentPlayerQuery':                        '8b59e806751e4e74359b416472925bb405601a626743084d2158af72cc3e7716',
		'CatalogQuery':                                           '40b62e4734f22a6009f1951fc1d03366b14a70833cb96a9a46c0e9b7043c67ef',
		'CatalogRefetchQuery':                                    'c4f5474dfc5d7937618d8a38357ad1e78cc83d6019833b1b68d86a0ce8d4b9e5',
		'ChallengeQuery':                                         '65252c7bbca148daf34de9a884e651bf9a5c1880a23f3d1e175a33f146b9f6dc',
		'ChallengeRefetchQuery':                                  '636c7f8180469847bbfe005afb589ee041bc8ca653c2a26d07987e582179fcad',
		'CheckinQuery':                                           '6dfce83d02761395758ae21454cb46924e81c22c3f151f91330b0602278a060e',
		'CheckinWithQRCodeMutation':                              '63a60eea7926b0f2600cfb64d8bf3b6736afc1e1040beabd5dfa40fbfdcb92d8',
		'ConfigureAnalyticsQuery':                                '2a9302bdd09a13f8b344642d4ed483b9464f20889ac17401e993dfa5c2bb3607',
		'CoopHistoryDetailQuery':                                 '824a1e22c4ad4eece7ad94a9a0343ecd76784be4f77d8f6f563c165afc8cf602',
		'CoopHistoryDetailRefetchQuery':                          '4bf516ccfd9a3f4efc32b215c59ae42c2a06dd2d8f73de95c2676dea6db74446',
		'CoopHistoryQuery':                                       '0f8c33970a425683bb1bdecca50a0ca4fb3c3641c0b2a1237aedfde9c0cb2b8f',
		'CoopPagerLatestCoopQuery':                               'bc8a3d48e91d5d695ef52d52ae466920670d4f4381cb288cd570dc8160250457',
		'CoopRecordBigRunRecordContainerPaginationQuery':         '4e357d607d98fa3b0f919f3aa0061af717c55c16017e31040647159bdb14601b',
		'CoopRecordQuery':                                        '940418e7b67b69420b7af50bdd292639e46fa8240ae57520a9cf7eed05a10760',
		'CoopRecordRefetchQuery':                                 '563536def9d127eb5c66eef94f9f3e10e5af00b0be6b8faa1692ae259e023fb3',
		'CreateMyOutfitMutation':                                 'b5257c5a3840cb01556750cbb56881d758534dfd91e9aec7c0232098fd767bb9',
		'DetailFestRecordDetailQuery':                            '02946c9d6dec617425ed41ee9a9bf467ea2ddfb85e0a36b09e4c3ea2e0b9ac5b',
		'DetailFestRefethQuery':                                  'dc5c1890cec78094d919e71621e9b4bc1ee06cfa99812dcacb401b8116a1ccad',
		'DetailFestVotingStatusRefethQuery':                      '4a24f9ff7b1c5a5c520872ce083c1623354c3ec092a0bf95c0dc1c12a1e3fb63',
		'DetailRankingQuery':                                     '2e1f603f6da371874a7473bb68418d9308f1fd2492e57fd2b7d9bbb80138f8c0',
		'DetailTabViewWeaponTopsArRefetchQuery':                  '0d97601d58e0eba18ea83fcce9789e35e10413344ccda7f9bb83129a2d7949f4',
		'DetailTabViewWeaponTopsClRefetchQuery':                  '42baca97f8038f51ffedc9bf837e820797d31c80cf4bac9b5b400fddb37ff3e1',
		'DetailTabViewWeaponTopsGlRefetchQuery':                  'a5237b76a33b7ee3eb79a2fe83f297e0e1324a3bf42bea9182ea49a5396bb053',
		'DetailTabViewWeaponTopsLfRefetchQuery':                  '2d23e55747f5365466b9563a89acb21851894b384fdbd33c80f8ee192b3d825b',
		'DetailTabViewXRankingArRefetchQuery':                    '0dc7b908c6d7ad925157a7fa60915523dab4613e6902f8b3359ae96be1ba175f',
		'DetailTabViewXRankingClRefetchQuery':                    '485e5decc718feeccf6dffddfe572455198fdd373c639d68744ee81507df1a48',
		'DetailTabViewXRankingGlRefetchQuery':                    '6ab0299d827378d2cae1e608d349168cd4db21dd11164c542d405ed689c9f622',
		'DetailTabViewXRankingLfRefetchQuery':                    'ca55206629f2c9fab38d74e49dda3c5452a83dd02a5a7612a2520a1fc77ae228',
		'DetailVotingStatusQuery':                                'e2aafab18dab26ba1b6d40838c6842201f6480d62f8f3dffecad8dd4c5b102c1',
		'DownloadSearchReplayQuery':                              '2805ee5182dd44c5114a1e6cfa57b2bcbbe9173c7e52069cc85a518de49c2191',
		'EventBattleHistoriesQuery':                              'e47f9aac5599f75c842335ef0ab8f4c640e8bf2afe588a3b1d4b480ee79198ac',
		'EventBattleHistoriesRefetchQuery':                       'a30281d08421b916902e4972f0d48d4d3346a92a68cbadcdb58b4e1a06273296',
		'EventMatchRankingPeriodQuery':                           'ad4097d5fb900b01f12dffcb02228ef6c20ddbfba41f0158bb91e845335c708e',
		'EventMatchRankingQuery':                                 '875a827a6e460c3cd6b1921e6a0872d8b95a1fce6d52af79df67734c5cc8b527',
		'EventMatchRankingRefetchQuery':                          'e9af725879a454fd3d5a191862ec3a544f552ae2d9bff6de6b212ac2676e8e14',
		'EventMatchRankingSeasonRefetchQuery':                    '5b563e5fb86ff7e537cc1ed86485049a41a710ca79af9c38113d41dda1d54643',
		'FestRecordQuery':                                        'c8660a636e73dcbf55c12932bc301b1c9db2aa9a78939ff61bf77a0ea8ff0a88',
		'FestRecordRefetchQuery':                                 '87ed3300bdecdb51090398d43ee0957e69b7bd1370ac38d03f6c7cb160b4586a',
		'FriendListQuery':                                        'ea1297e9bb8e52404f52d89ac821e1d73b726ceef2fd9cc8d6b38ab253428fb3',
		'FriendListRefetchQuery':                                 '411b3fa70a9e0ff083d004b06cc6fad2638a1a24326cbd1fb111e7c72a529931',
		'GesotownQuery':                                          'd6f94d4c05a111957bcd65f8649d628b02bf32d81f26f1d5b56eaef438e55bab',
		'GesotownRefetchQuery':                                   '681841689c2d0f8d3355b71918d6c9aedf68484dfcb06b144407df1c4873dea0',
		'HeroHistoryQuery':                                       '71019ce4389463d9e2a71632e111eb453ca528f4f794aefd861dff23d9c18147',
		'HeroHistoryRefetchQuery':                                'c6cb0b7cfd8721e90e3a85d3340d190c7f9c759b6b5e627900f5456fec61f6ff',
		'HistoryRecordQuery':                                     '0a62c0152f27c4218cf6c87523377521c2cff76a4ef0373f2da3300079bf0388',
		'HistoryRecordRefetchQuery':                              'a5d80de05d1d4bfce67a1fb0801495d8bc6bba6fd780341cb90ddfeb1249c986',
		'HomeQuery':                                              '51fc56bbf006caf37728914aa8bc0e2c86a80cf195b4d4027d6822a3623098a8',
		'JourneyChallengeDetailQuery':                            'ed634e52cd478ebc9d77d84831665aabfac14ac74bb343aa73c310539894169a',
		'JourneyChallengeDetailRefetchQuery':                     'c7e4044cc4320e4ae44ccda1b7eb74897d213628c4e5d2f2863df5f8e8a9478d',
		'JourneyQuery':                                           'c0cd04d2f0b00444853bae0d7e7f1ac534dfd7ff593c738ab9ba4456b1e85f8a',
		'JourneyRefetchQuery':                                    'd5fc5dd3a144139e89815b9e3af6499f58e5fc5185876840dd6edadb0ca214b4',
		'LatestBattleHistoriesQuery':                             'b24d22fd6cb251c515c2b90044039698aa27bc1fab15801d83014d919cd45780',
		'LatestBattleHistoriesRefetchQuery':                      '58bf17200ca97b55d37165d44902067b617d635e9c8e08e6721b97e9421a8b67',
		'MyOutfitDetailQuery':                                    'e2c9ea77f0469cb8109c54e93f3f35c930dfeb5b79cbf639397828a805ad9248',
		'MyOutfitsQuery':                                         '5b32bb88c47222522d2bc3643b92759644f890a70189a0884ea2d456a8989342',
		'MyOutfitsRefetchQuery':                                  '565bc1f16c0a5088d41b203775987c70756296747ba905c3e1c0ce8f3f27f925',
		'PagerLatestVsDetailQuery':                               '73462e18d464acfdf7ac36bde08a1859aa2872a90ed0baed69c94864c20de046',
		'PagerUpdateBattleHistoriesByVsModeQuery':                'ac6561ff575363efcc9b876cf179929203dab17d3f25ab293a1123f4637e1dc7',
		'PhotoAlbumQuery':                                        '62383a0595fab69bf49a2a6877bc47acc081bfa065cb2eae28aa881980bb30b2',
		'PhotoAlbumRefetchQuery':                                 '0819c222d0b68fbcc7706f60b98e797da7d1fce637b45b3bdadca1ccdb692c86',
		'PrivateBattleHistoriesQuery':                            'fef94f39b9eeac6b2fac4de43bc0442c16a9f2df95f4d367dd8a79d7c5ed5ce7',
		'PrivateBattleHistoriesRefetchQuery':                     '3dd1b491b2b563e9dfc613e01f0b8e977e122d901bc17466743a82b7c0e6c33a',
		'RankingHoldersFestTeamRankingHoldersPaginationQuery':    '34460535ce2b699ed0617d67e22a7e3290fd30041559bf6f05d408d06f1c9938',
		'RegularBattleHistoriesQuery':                            '2fe6ea7a2de1d6a888b7bd3dbeb6acc8e3246f055ca39b80c4531bbcd0727bba',
		'RegularBattleHistoriesRefetchQuery':                     'e818519b50e877ac6aeaeaf19e0695356f28002ad4ccf77c1c4867ef0df9a6d7',
		'ReplayModalReserveReplayDownloadMutation':               '07e94ba8076b235d9b16c9e8d1714dfffbd4441c17225c36058b8a7ba44458b1',
		'ReplayQuery':                                            '3af48164d1176e8a88fb5321f5fb2daf9dde00b314170f1848a30e1825fc828e',
		'ReplayUploadedReplayListRefetchQuery':                   '1e42b2238c385b5db29717b98d0df5934c75e8807545091d97200127ed1ecef0',
		'SaleGearDetailOrderGesotownGearMutation':                'bb716c3be6e85331741d7e2f9b36a6c0de92ca1b8382418744c1540fec7c8f57',
		'SaleGearDetailQuery':                                    'b42e70a6873aa716d089f2c5ea219083d30f0fff6ed15b8f5630c01ef7a32015',
		'SettingQuery':                                           '8473b5eb2c2048f74eb48b0d3e9779f44febcf3477479625b4dc23449940206b',
		'StageRecordQuery':                                       'c8b31c491355b4d889306a22bd9003ac68f8ce31b2d5345017cdd30a2c8056f3',
		'StageRecordsRefetchQuery':                               '25dbf592793a590b6f8cfb0a62823aa02429b406a590333627d8ea703b190dfd',
		'StageScheduleQuery':                                     '9b6b90568f990b2a14f04c25dd6eb53b35cc12ac815db85ececfccee64215edd',
		'SupportButton_SupportChallengeMutation':                 '3165b76878d09ea55a7194e675397a5e030a2a89b98a0e81af77e346c625c4fd',
		'UpdateMyOutfitMutation':                                 'b83ed5a9b58252c088d3aac7f28a34a59acfbaa61b187ee3eebfe8506aa720f9',
		'VotesUpdateFestVoteMutation':                            'b0830a3c3c9d8aa6ed83e200aed6b008f992acdba4550ab4399417c1f765e7e3',
		'VsHistoryDetailPagerRefetchQuery':                       '973ca7012d8e94da97506cd39dfbb2a45eaae6e382607b650533d4f5077d840d',
		'VsHistoryDetailQuery':                                   'f893e1ddcfb8a4fd645fd75ced173f18b2750e5cfba41d2669b9814f6ceaec46',
		'WeaponRecordQuery':                                      '974fad8a1275b415c3386aa212b07eddc3f6582686e4fef286ec4043cdf17135',
		'WeaponRecordsRefetchQuery':                              '7d7194a98cb7b0b235f15f98a622fab4945992fd268101e24443db82569dd25d',
		'XBattleHistoriesQuery':                                  'eb5996a12705c2e94813a62e05c0dc419aad2811b8d49d53e5732290105559cb',
		'XBattleHistoriesRefetchQuery':                           'a175dc519f551c0bbeed04286194dc12b1a05e3117ab73f6743e5799e91f903a',
		'XRankingDetailQuery':                                    '90932ee3357eadab30eb11e9d6b4fe52d6b35fde91b5c6fd92ba4d6159ea1cb7',
		'XRankingDetailRefetchQuery':                             '00e8e962cc65795c6480d10caddaee7e0262d5cdf81e5958ff8f3359bd2f9743',
		'XRankingQuery':                                          'a5331ed228dbf2e904168efe166964e2be2b00460c578eee49fc0bc58b4b899c',
		'XRankingRefetchQuery':                                   '5a469004feb402a1d44a10820b647def2d4eb320436f6add4431194a34d0b497',
		'myOutfitCommonDataEquipmentsQuery':                      '45a4c343d973864f7bb9e9efac404182be1d48cf2181619505e9b7cd3b56a6e8',
		'myOutfitCommonDataFilteringConditionQuery':              'ac20c44a952131cb0c9d00eda7bc1a84c1a99546f0f1fc170212d5a6bb51a426',
		'refetchableCoopHistory_coopResultQuery':                 'bdb796803793ada1ee2ea28e2034a31f5c231448e80f5c992e94b021807f40f8',
		'useCurrentFestQuery':                                    '980af9d079ce2a6fa63893d2cd1917b70a229a222b24bbf8201f48d814ff48f0',
		'useShareMyOutfitQuery':                                  '5502b09121f5e18bec8fefbe80cce21e1641624b579c57c1992b30dcff612b44',
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

