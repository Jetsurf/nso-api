import requests, json, urllib

class ACNH()
	def __init__(self):
		self.acnh_user = {
			'Host': 'web.sd.lp1.acbaa.srv.nintendo.net',
			'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36',
			'Accept': 'application/json, text/plain, */*',
			'Connection': 'keep-alive',
			'Referer': 'https://web.sd.lp1.acbaa.srv.nintendo.net/?lang=en-US&na_country=US&na_lang=en-US',
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'en-us'
		}
		self.acnh_user_auth = {
			'Host': 'web.sd.lp1.acbaa.srv.nintendo.net',
			'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36',
			'Accept': 'application/json, text/plain, */*',
			'Connection': 'keep-alive',
			'Referer': 'https://web.sd.lp1.acbaa.srv.nintendo.net/players/passport',
			'Authorization' : 'tmp',
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'en-us'
		}
		self.s2_user_gcookie = {
			'_dnt' : '1',
			'_ga' : 'GA1.2.235595523.1520818620',
			'_gtoken' : 'tmp'
		}
		self.s2_user_pcookie = {
			'_dnt' : '1',
			'_ga' : 'GA1.2.235595523.1520818620',
			'_gtoken' : 'tmp',
			'_park_session' : 'tmp'
		}

	