import time
import requests
import re

from .nso_expiring_token import NSO_Expiring_Token

class NSO_API_S2:
	def __init__(self, nso_api):
		self.nso_api = nso_api
		self.game_id = 5741031244955648  # Splatoon 2
		self.web_service_token = None
		self.iksm_session_token = None
		self.xid = None

	def get_keys(self):
		keys = {}
		keys['web_service_token'] = self.web_service_token.to_hash() if self.web_service_token else None
		keys['iksm_session_token'] = self.iksm_session_token.to_hash() if self.iksm_session_token else None
		keys['x-unique-id'] = self.xid
		return keys

	def set_keys(self, keys):
		if keys is None:
			return
		self.web_service_token = NSO_Expiring_Token.from_hash(keys['web_service_token']) if keys.get('web_service_token') else None
		self.iksm_session_token = NSO_Expiring_Token.from_hash(keys['iksm_session_token']) if keys.get('iksm_session_token') else None
		self.xid = keys.get('x-unique-id') if keys.get('x-unique-id') else None

	def create_iksm_session_token_request(self):
		if not self.web_service_token:
			raise Exception("No web_service_token")

		headers = {}
		headers['Host'] = 'app.splatoon2.nintendo.net'
		headers['User-Agent'] = f'com.nintendo.znca/{self.nso_api.get_app_version()} (Android/7.1.2)'
		headers['Content-Type'] = 'application/json; charset=utf-8'
		headers['X-Platform'] = 'Android'
		headers['X-ProductVersion'] = self.nso_api.get_app_version()
		headers['x-gamewebtoken'] = self.web_service_token.value
		headers['x-isappanalyticsoptedin'] = 'false'
		headers['X-Requested-With'] = 'com.nintendo.znca'
		headers['Connection'] = 'keep-alive'

		req = requests.Request('GET', 'https://app.splatoon2.nintendo.net', headers = headers)
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

	# Gets the iksm_session_token. This is actually an HTTP cookie.
	def ensure_iksm_session_token(self):
		if self.iksm_session_token and self.iksm_session_token.is_fresh():
			return True

		response = self.nso_api.do_http_request(self.create_iksm_session_token_request())
		if not response:
			return False

		iksm_session_token = None
		for cookie in response.cookies:
			if cookie.name == 'iksm_session':
				iksm_session_token = NSO_Expiring_Token(cookie.value, expiretime = cookie.expires)

		if not iksm_session_token:
			self.nso_api.errors.append("Expected iksm_session cookie but didn't get one")
			return False

		data = re.search("data-unique-id=\"([0-9]*?)\"", response.text)
		xid = data.group(1)
		if not xid:
			self.nso_api.errors.append("Expected data-unique-id, got none")
			return False

		self.xid = xid
		self.iksm_session_token = iksm_session_token
		self.nso_api.notify_user_data_update()
		return True

	def get_player_json(self, url, referer = None):
		if not self.ensure_web_service_token():
			self.nso_api.errors.append("Could not get S2 web_service_token")
			return None

		if not self.ensure_iksm_session_token():
			self.nso_api.errors.append("Could not get S2 iksm_session_token")
			return None

		headers = {}
		headers['Host'] = 'app.splatoon2.nintendo.net'
		headers['x-requested-with'] = 'XMLHttpRequest'
		headers['x-unique-id'] = self.xid
		headers['x-timezone-offset'] = str(int((time.mktime(time.gmtime()) - time.mktime(time.localtime()))/60))
		headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36'
		headers['Accept'] = '*/*'
		headers['Referer'] = 'https://app.splatoon2.nintendo.net/home'
		headers['Accept-Encoding'] = 'gzip, deflate'
		headers['Accept-Language'] = 'en-us'

		req = requests.Request('GET', url, headers = headers, cookies = dict(iksm_session = self.iksm_session_token.value))
		return self.nso_api.do_json_request(req)

	def get_store_json(self):
		if not self.ensure_web_service_token():
			self.nso_api.errors.append("Could not get S2 web_service_token")
			return None

		if not self.ensure_iksm_session_token():
			self.nso_api.errors.append("Could not get S2 iksm_session_token")
			return None

		headers = {}
		headers['x-requested-with'] = 'XMLHttpRequest'
		headers['x-unique-id'] = self.xid
		headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36'
		headers['Referer'] = f"https://app.splatoon2.nintendo.net/home/shop"
		headers['Accept-Encoding'] = 'gzip, deflate, br'

		req = requests.Request('GET', "https://app.splatoon2.nintendo.net/api/onlineshop/merchandises", headers = headers, cookies = dict(iksm_session = self.iksm_session_token.value))
		return self.nso_api.do_json_request(req, expect_status=[200, 400]) #400 returns w/ item on order but override false

	def post_store_json(self, merchid, confirmation):
		if not self.ensure_web_service_token():
			self.nso_api.errors.append("Could not get S2 web_service_token")
			return None

		if not self.ensure_iksm_session_token():
			self.nso_api.errors.append("Could not get S2 iksm_session_token")
			return None

		headers = {}
		headers['Origin'] = 'https://app.splatoon2.nintendo.net'
		headers['x-requested-with'] = 'XMLHttpRequest'
		headers['x-unique-id'] = self.xid
		headers['x-timezone-offset'] = str(int((time.mktime(time.gmtime()) - time.mktime(time.localtime()))/60))
		headers['User-Agent'] = 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36'
		headers['Accept'] = '*/*'
		headers['Referer'] = f"https://app.splatoon2.nintendo.net/home/shop/{merchid}"
		headers['Accept-Encoding'] = 'gzip, deflate, br'
		headers['Accept-Language'] = 'en-us'
		
		if confirmation:
			payload = { "override" : 1 }
		else:
			payload = { "override" : 0 }

		url = f"https://app.splatoon2.nintendo.net/api/onlineshop/order/{merchid}"
		req = requests.Request('POST', url, headers = headers, cookies = dict(iksm_session = self.iksm_session_token.value), data=payload)
		return self.nso_api.do_json_request(req, expect_status=[200, 400]) #400 returns w/ item on order but override false

	def do_records_request(self):
		return self.get_player_json("https://app.splatoon2.nintendo.net/api/records")

	def do_coop_request(self):
		return self.get_player_json("https://app.splatoon2.nintendo.net/api/coop_results", "https://app.splatoon2.nintendo.net/coop")

	def get_all_battles(self):
		return self.get_player_json("https://app.splatoon2.nintendo.net/api/results")

	def get_full_battle(self, battleid):
		return self.get_player_json(f"https://app.splatoon2.nintendo.net/api/results/{battleid}")

	def get_store_merchandise(self):
		return self.get_store_json()

	# Backwards compatibility
	def get_store_merchendise(self):
		print("nso_api_s2: Please call 'get_store_merchandise', not 'get_store_merchendise'")
		return self.get_store_merchandise()

	def post_store_purchase(self, merchid, confirmation=False):
		return self.post_store_json(merchid, confirmation)

	def get_ranks(self):
		records = self.do_records_request()
		if not records:
			return

		name = records['records']['player']['nickname']
		szrank = records['records']['player']['udemae_zones']['name']
		if szrank == "S+":
			szrank += str(records['records']['player']['udemae_zones']['s_plus_number'])

		rmrank = records['records']['player']['udemae_rainmaker']['name']
		if rmrank == "S+":
			rmrank += str(records['records']['player']['udemae_rainmaker']['s_plus_number'])

		tcrank = records['records']['player']['udemae_tower']['name']
		if tcrank == "S+":
			tcrank += str(records['records']['player']['udemae_tower']['s_plus_number'])

		cbrank = records['records']['player']['udemae_clam']['name']
		if cbrank == "S+":
			cbrank += str(records['records']['player']['udemae_clam']['s_plus_number'])

		return { "SZ": szrank, "RM": rmrank, "TC": tcrank, "CB": cbrank, 'name': name }

	def get_map_stats(self, mapid):
		data = self.do_records_request()
		allmapdata = data['records']['stage_stats']
		themapdata = None
		for i in allmapdata:
			if int(i) == mapid:
				themapdata = allmapdata[i]
				break
		
		playername = data['records']['player']['nickname']
		mapname = themapdata['stage']['name']
		rmwin = themapdata['hoko_win']
		rmloss = themapdata['hoko_lose']
		szwin = themapdata['area_win']
		szloss = themapdata['area_lose']
		tcwin = themapdata['yagura_win']
		tcloss = themapdata['yagura_lose']
		cbwin = themapdata['asari_win']
		cbloss = themapdata['asari_lose']
		image = themapdata['stage']['image']

		if (rmwin + rmloss) != 0:
			rmpercent = int(rmwin / (rmwin + rmloss) * 100)
		else:
			rmpercent = 0
		if (szwin + szloss) != 0:
			szpercent = int(szwin / (szwin + szloss) * 100)
		else:
			szpercent = 0
		if (tcwin + tcloss) != 0:
			tcpercent = int(tcwin / (tcwin + tcloss) * 100)
		else:
			tcpercent = 0
		if (cbwin + cbloss) != 0:
			cbpercent = int(cbwin / (cbwin + cbloss) * 100)
		else:
			cbpercent = 0

		rmdict = { 'wins' : rmwin, 'losses' : rmloss, 'percent' : rmpercent }
		szdict = { 'wins' : szwin, 'losses' : szloss, 'percent' : szpercent }
		tcdict = { 'wins' : tcwin, 'losses' : tcloss, 'percent' : tcpercent }
		cbdict = { 'wins' : cbwin, 'losses' : cbloss, 'percent' : cbpercent }

		return { 'SZ' : szdict, "TC" : tcdict, "RM" : rmdict, "CB" : cbdict, 'map_name' : mapname, 'player_name' : playername, 'image' : image }

	def get_weapon_stats(self, weapid):
		data = self.do_records_request()
		weapondata = data['records']['weapon_stats']
		name = data['records']['player']['nickname']
		retData = {}
		retData['player_name'] = name

		theweapdata = None
		gotweap = False
		#TODO: Check if there is a cleaner way
		for i in weapondata:
			if int(i) == weapid:
				gotweap = True
				theweapdata = weapondata[i]
				break

		if not gotweap:
			retData['weapon_data'] = None
			return retData

		wins = theweapdata['win_count']
		loss = theweapdata['lose_count']
		if (wins + loss) != 0:
			winper = int(wins / (wins + loss) * 100)
		else:
			winper = 0

		retData['weapon_data'] = {}
		retData['weapon_data']['name'] = theweapdata['weapon']['name']
		retData['weapon_data']['wins'] = wins
		retData['weapon_data']['losses'] = loss
		retData['weapon_data']['percent'] = winper
		retData['weapon_data']['freshness_current'] = theweapdata['win_meter']
		retData['weapon_data']['freshness_max'] = theweapdata['max_win_meter']
		retData['weapon_data']['turf_inked'] = theweapdata['total_paint_point']
		retData['weapon_data']['image'] = theweapdata['weapon']['image']
		return retData

	def get_player_stats(self):
		data = self.do_records_request()

		retData = {}
		retData['name'] = data['records']['player']['nickname']
		retData['species'] = data['records']['player']['player_type']['species'].capitalize()
		retData['gender'] = data['records']['player']['player_type']['style']

		retData['turf_stats'] = {}
		retData['turf_stats']['inked_total'] = data['challenges']['total_paint_point_octa'] + data['challenges']['total_paint_point']
		retData['turf_stats']['inked_squid'] = data['challenges']['total_paint_point']
		retData['turf_stats']['inked_octo'] = data['challenges']['total_paint_point_octa']

		retData['wl_stats'] = {}
		retData['wl_stats']['total_wins'] = data['records']['win_count']
		retData['wl_stats']['total_loss'] = data['records']['lose_count']
		retData['wl_stats']['recent_wins'] = data['records']['recent_win_count']
		retData['wl_stats']['recent_loss'] = data['records']['recent_lose_count']

		if retData['wl_stats']['recent_loss'] + retData['wl_stats']['recent_wins'] > 0:
			recentperc = "{:.0%}".format(retData['wl_stats']['recent_wins']/(retData['wl_stats']['recent_wins'] + retData['wl_stats']['recent_loss']))
			totalperc = "{:.0%}".format(retData['wl_stats']['total_wins']/(retData['wl_stats']['total_loss'] + retData['wl_stats']['total_loss']))
		else:
			recentperc = "0%"
			totalperc = "0%"

		retData['wl_stats']['recent_percent'] = recentperc
		retData['wl_stats']['total_percent'] = totalperc

		retData['league_stats'] = {}
		retData['league_stats']['max_rank_team'] = data['records']['player']['max_league_point_team']
		retData['league_stats']['max_rank_pair'] = data['records']['player']['max_league_point_pair']
		retData['league_stats']['pair_gold'] = data['records']['league_stats']['pair']['gold_count']
		retData['league_stats']['pair_silver'] = data['records']['league_stats']['pair']['silver_count']
		retData['league_stats']['pair_bronze'] = data['records']['league_stats']['pair']['bronze_count']
		retData['league_stats']['pair_none'] = data['records']['league_stats']['pair']['no_medal_count']
		retData['league_stats']['team_gold'] = data['records']['league_stats']['team']['gold_count']
		retData['league_stats']['team_silver'] = data['records']['league_stats']['team']['silver_count']
		retData['league_stats']['team_bronze'] = data['records']['league_stats']['team']['bronze_count']
		retData['league_stats']['team_none'] = data['records']['league_stats']['team']['no_medal_count']

		topweap = None
		topink = 0
		for i in data['records']['weapon_stats']:
			j = data['records']['weapon_stats'][i]
			if topink < int(j['total_paint_point']):
				topink = int(j['total_paint_point'])
				topweap = j

		retData['top_weapon'] = {}
		retData['top_weapon']['total_inked'] = topink
		retData['top_weapon']['name'] = topweap['weapon']['name']

		return retData

	def get_sr_stats(self):
		data = self.do_coop_request()
		jobresults = data['results']
		retData = {}
		retData['player_name'] = data['results'][0]['my_result']['name']
		#This provides a brief stats summary, not advanced stats
		jobcard = data['summary']['card']
		retData['rank_name'] = data['summary']['stats'][0]['grade']['name']
		retData['rank_points'] = data['summary']['stats'][0]['grade_point']

		#TODO: Clean this up? Calculates all stats for last 50 maps
		retData['boss_stats'] = {}
		retData['boss_stats']['Steelhead'] = 0
		retData['boss_stats']['Stinger'] = 0
		retData['boss_stats']['Flyfish'] = 0
		retData['boss_stats']['Steel Eel'] = 0
		retData['boss_stats']['Scrapper'] = 0
		retData['boss_stats']['Maws'] = 0
		retData['boss_stats']['Drizzler'] = 0
		retData['boss_stats']['Griller'] = 0
		retData['boss_stats']['Goldie'] = 0
		retData['overall_stats'] = {}
		retData['overall_stats']['power_eggs_total'] = jobcard['ikura_total']
		retData['overall_stats']['golden_eggs_total'] = jobcard['golden_ikura_total']
		retData['overall_stats']['help_total'] = jobcard['help_total']
		retData['overall_stats']['matches_total'] = jobcard['job_num']
		retData['overall_stats']['points_total'] = jobcard['kuma_point_total']
		retData['recent_stats'] = {}
		retData['recent_stats']['help_total'] = 0
		retData['recent_stats']['deaths_total'] = 0
		retData['recent_stats']['golden_eggs_total'] = 0
		retData['recent_stats']['power_eggs_total'] = 0
		matches = 0
		hazardpts = 0

		for i in jobresults:
			matches += 1
			retData['recent_stats']['deaths_total'] += i['my_result']['dead_count']
			retData['recent_stats']['help_total'] += i['my_result']['help_count']
			hazardpts += i['danger_rate']
			retData['recent_stats']['golden_eggs_total'] += i['my_result']['golden_ikura_num']
			retData['recent_stats']['power_eggs_total'] += i['my_result']['ikura_num']
			for j in i['my_result']['boss_kill_counts']:
				y = i['my_result']['boss_kill_counts'][j]
				retData['boss_stats'][y['boss']['name']] += y['count']

		retData['recent_stats']['matches_total'] = matches
		retData['recent_stats']['hazard_average'] = int(hazardpts / matches)
		retData['recent_stats']['golden_eggs_average'] = int(retData['recent_stats']['golden_eggs_total'] / matches)
		retData['recent_stats']['power_eggs_average'] = int(retData['recent_stats']['power_eggs_total'] / matches)
		retData['recent_stats']['deaths_average'] = int(retData['recent_stats']['deaths_total'] / matches)
		retData['recent_stats']['help_average'] = int(retData['recent_stats']['help_total'] / matches)

		return retData
