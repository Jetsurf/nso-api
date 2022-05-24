import time
import requests, json

class Splatoon2():
	def __init__(self, *args, **options):
		self.auth = options.get('auth')
		self.app_timezone_offset = str(int((time.mktime(time.gmtime()) - time.mktime(time.localtime()))/60))
		self.s2_player = {
			'Host': 'app.splatoon2.nintendo.net',
			'x-unique-id': '8386546935489260343',
			'x-requested-with': 'XMLHttpRequest',
			'x-timezone-offset': self.app_timezone_offset,
			'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36',
			'Accept': '*/*',
			'Referer': 'https://app.splatoon2.nintendo.net/home',
			'Accept-Encoding': 'gzip, deflate',
			'Accept-Language': 'en-us'
		}
		self.s2_shop = {
			"origin": "https://app.splatoon2.nintendo.net",
			"x-unique-id": '16131049444609162796',
			"x-requested-with": "XMLHttpRequest",
			"x-timezone-offset": self.app_timezone_offset,
			"User-Agent": "Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36",
			"Accept": "*/*",
			"Referer": "https://app.splatoon2.nintendo.net/results",
			"Accept-Encoding": "gzip, deflate",
			"Accept-Language": "en-US"
		}

		self.s2_coop = {
			'Host': 'app.splatoon2.nintendo.net',
			'x-unique-id': '8386546935489260343',
			'x-requested-with': 'XMLHttpRequest',
			'x-timezone-offset': self.app_timezone_offset,
			'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36',
			'Accept': '*/*',
			'Referer': 'https://app.splatoon2.nintendo.net/coop',
			'Accept-Encoding': 'gzip, deflate',
			'Accept-Language': 'en-us'
		}

	def do_get_request(self, snowflake, url, header):
		response = requests.get(url, headers=header, cookies=dict(iksm_session=self.auth.getGameKey(snowflake, 's2.iksm')))
		thejson = json.loads(response.text)
		if 'AUTHENTICATION_ERROR' in str(thejson):
			iksm = self.auth.doGameKeyRefresh(snowflake)
			if iksm == None:
				return None
			response = requests.get(url, headers=header, cookies=dict(iksm_session=iksm['iksm']))
			thejson = json.loads(response.text)
			if 'AUTHENTICATION_ERROR' in str(thejson):
				return None
		return thejson

	def get_player_records(self, snowflake) -> dict:
		url = "https://app.splatoon2.nintendo.net/api/records"
		header = self.s2_player
		return self.do_get_request(snowflake, url, header)

	def get_salmon_run(self, snowflake) -> dict:
		url = "https://app.splatoon2.nintendo.net/api/coop_results"
		header = self.s2_coop
		return self.do_get_request(snowflake, url, header)

	def get_battles(self, snowflake) -> dict:
		url = "https://app.splatoon2.nintendo.net/api/results"
		header = self.s2_player
		return self.do_get_request(snowflake, url, header)

	def get_full_battles(self, battleid, snowflake) -> dict:
		url = f"https://app.splatoon2.nintendo.net/api/results/{battleid}"
		header = self.s2_player
		return self.do_get_request(snowflake, url, header)

	def get_store_merch(self, snowflake) -> dict:
		url = "https://app.splatoon2.nintendo.net/api/onlineshop/merchandises"
		header = self.s2_player
		return self.do_get_request(snowflake, url, header)

	def order_from_store(self, gearid, override=False, snowflake=None) -> dict:
		payload = { "override" : "1" if override else "0" }
		response = requests.post(f"https://app.splatoon2.nintendo.net/api/onlineshop/order/{gearid}", headers=self.s2_player, cookies=dict(iksm_session=self.auth.getGameKey(snowflake, 's2').iksm['iksm']), data=payload)
		thejson = json.loads(response.text)
		print(f"pynso: {thejson}")
		if 'AUTHENTICATION_ERROR' in str(thejson):
			iksm = self.auth.doGameKeyRefresh(snowflake)
			if iksm == None:
				return None
			response = requests.post(f"https://app.splatoon2.nintendo.net/api/onlineshop/order/{gearid}", headers=self.s2_player, cookies=dict(iksm_session=iksm['iksm']))
			thejson = json.loads(response.text)
			if 'AUTHENTICATION_ERROR' in str(thejson):
				return None
		return thejson