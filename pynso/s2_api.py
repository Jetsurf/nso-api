import time
import requests, json

class Splatoon2():
	def __init__(self):
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
		self.ah_s2_shop = {
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

		self.ah_s2_coop = {
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

	def get_player_stats(self, iksm) -> dict:
		print(type(iksm))
		results_list = requests.get("https://app.splatoon2.nintendo.net/api/records", headers=self.s2_player, cookies=dict(iksm_session=iksm['iksm']))
		thejson = json.loads(results_list.text)
		return thejson

	def get_salmon_run(self, iksm) -> dict:
		pass

	def get_battles(self, iksm) -> dict:
		pass

	def get_full_battles(self, iksm) -> dict:
		pass
