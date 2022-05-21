from datetime import datetime
import googleplay
import stringcrypt
import apscheduler

class nso_authentication():
	def __init__(self,  *args, **options):
		self.session = requests.Session()
		self.pynso_pool = options.get('pynso_pool')
		self.scheduler = BackgroundScheduler()
		self.string_crypt = stringcrypt.StringCrypt()
		self.scheduler.add_job(self.updateAppVersion, 'cron', hour="3", minute='0', second='35', timezone='UTC')
		self.keyPath = '/home/dbot/db-secret-key.hex'

	def ensureEncryptionKey():
		if os.path.isfile(self.keyPath):
			print("pynso: Found secret key file...")
			stringCrypt.readSecretKeyFile(self.keyPath)
		else:
			print("pynso: Creating new secret key file...")
			stringCrypt.writeSecretKeyFile(self.keyPath)

	def getAppVersion(self):
		cur = self.pynso_pool.cursor()

		cur.execute("SELECT version, UNIX_TIMESTAMP(updatetime) AS updatetime FROM nso_app_version")
		row = cur.fetchone()
		cur.close()

		if row:
			return {'version': row[0], 'updatetime': row[1]}

		return None

	def updateAppVersion(self):
		oldInfo = self.getAppVersion()
		if oldInfo != None:
			age = time.time() - oldInfo['updatetime']
			if age < 3600:
				print("Skipping NSO version check -- cached data is recent")
				return

		gp = googleplay.GooglePlay()
		newVersion = gp.getAppVersion("com.nintendo.znca")
		if newVersion == None:
			print(f"Couldn't retrieve NSO app version?")
			return

		cur = self.pynso_pool.cursor()

		if (oldInfo == None) or (oldInfo['version'] != newVersion):
			# Version was updated
			cur.execute("DELETE FROM nso_app_version")
			cur.execute("INSERT INTO nso_app_version (version, updatetime) VALUES (%s, NOW())", (newVersion,))
			print(f"pynso: Updated NSO version: {oldInfo['version'] if oldInfo else '(none)'} -> {newVersion}")
		else:
			# No version change, so just bump the timestamp
			cur.execute("UPDATE nso_app_version SET updatetime = NOW()")

		cur.commit()
		cur.close()

	def getGameKeys(self, snowflake):
		cur = self.pynso_pool.cursor()
		cur.execute("SELECT game_keys FROM tokens WHERE (snowflake = %s) LIMIT 1", (str(snowflake),))
		row = cur.fetchone()
		cur.close(cur)

		if (row == None) or (row[0] == None):
			return {}  # No keys

		ciphertext = row[0]
		plaintext = self.stringCrypt.decryptString(ciphertext)
		#print(f"getGameKeys: {ciphertext} -> {plaintext}")
		keys = json.loads(plaintext)
		return keys

	# Retrieves a single game key with a dotted path (e.g. "s2.iksm")
	def getGameKey(self, showflake, path):
		hash = self.getGameKeys(snowflake)
		parts = path.split('.')
		for k in parts:
			hash = hash.get(k)
			if not hash:
				return None
		return hash

	def __setGameKeys(self, snowflake, keys):
		plaintext = json.dumps(keys)
		ciphertext = self.stringCrypt.encryptString(plaintext)
		#print(f"setGameKeys: {plaintext} -> {ciphertext}")

		cur = self.pynso_pool.cursor()
		cur.execute("UPDATE tokens SET game_keys = %s, game_keys_time = NOW() WHERE (snowflake = %s)", (ciphertext, snowflake))
		cur.commit()
		cur.close()

	# Stores the given data at the dotted path.
	def __setGameKey(self, snowflake, path, data):
		hash = self.getGameKeys(snowflake)
		#print(f"pre hash: {hash}")
		parts = path.split(".")
		for k in parts[0:-1]:
			if hash.get(k) == None:
				hash[k] = {}
			hash = hash[k]
		hash[parts[-1]] = data
		#print(f"post hash: {hash}")
		self.__setGameKeys(snowflake, hash)

	def __checkDuplicate(self, id, cur):
		cur.execute("SELECT COUNT(*) FROM tokens WHERE snowflake = %s", (str(id),))
		count = cur.fetchone()
		if count[0] > 0:
			return True
		else:
			return False

	def checkSessionPresent(self, snowflake):
		cur = self.pynso_pool.cursor()
		ret = self.__checkDuplicate(snowflake, cur)
		cur.close(cur)
		return ret

	def deleteTokens(self, snowflake):
		cur = self.pynso_pool.cursor()
		print("Deleting token")
		stmt = "DELETE FROM tokens WHERE snowflake = %s"
		input = (snowflake,)
		cur.execute(stmt, input)
		if cur.lastrowid != None:
			cur.commit(cur)
			cur.close()
			return True
		else:
			cur.rollback()
			cur.close()
			return False

	def loginUrl(self):
		auth_state = base64.urlsafe_b64encode(os.urandom(36))
		auth_code_verifier = base64.urlsafe_b64encode(os.urandom(32))
		auth_cv_hash = hashlib.sha256()
		auth_cv_hash.update(auth_code_verifier.replace(b"=", b""))
		auth_code_challenge = base64.urlsafe_b64encode(auth_cv_hash.digest())
		head = {
			'Host':                      'accounts.nintendo.com',
			'Connection':                'keep-alive',
			'Cache-Control':             'max-age=0',
			'Upgrade-Insecure-Requests': '1',
			'User-Agent':                'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36',
			'Accept':                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8n',
			'DNT':                       '1',
			'Accept-Encoding':           'gzip,deflate,br',
		}
		body = {
			'state':                                auth_state,
			'redirect_uri':                         'npf71b963c1b7b6d119://auth',
			'client_id':                            '71b963c1b7b6d119',
			'scope':                                'openid user user.birthday user.mii user.screenName',
			'response_type':                        'session_token_code',
			'session_token_code_challenge':         auth_code_challenge.replace(b"=", b""),
			'session_token_code_challenge_method': 'S256',
			'theme':                               'login_form'
		}
		r = self.session.get('https://accounts.nintendo.com/connect/1.0.0/authorize', headers=head, params=body)

		post_login = r.history[0].url

		return {'auth_code_verifier' : auth_code_verifier, 'url' : post_login}
		
	def postLogin(self, snowflake, returnedUrl, auth_code_verifier) -> bool:
		cur = self.pynso_pool.cursor()
		session_token_code = re.search('session_token_code=(.*)&', returnedUrl)
		if session_token_code == None:
			cur.close()
			print(f"pynso: authentication: Issue with account url: {str(accounturl)}")
			return False
		session_token_code = self.__get_session_token(session_token_code.group(0)[19:-1], auth_code_verifier)
		if session_token_code == None:
			print("pynso: authentication: no session token code")
			cur.close()
			return False
		else:			
			ciphertext = self.stringCrypt.encryptString(session_token_code)
			cur.execute("INSERT INTO tokens (snowflake, session_time, session_token) VALUES(%s, NOW(), %s)", (snowflake, ciphertext, ))
			if cur.lastrowid != None:
				cur.commit()
				cur.close()
				if self.doGameKeyRefresh(snowflake, 'nso'):
					return True
				else:
					return False
			else:
				cur.rollback()
				cur.close()
				return False

	#This method will always return the root key path for a game
	def doGameKeyRefresh(self, snowflake, game='s2') -> Optional[dict]:
		session_token = self.__get_session_token_mysql(snowflake)
		keys = self.__setup_nso(session_token, game)

		if keys == 500:
			if isinstance(snowflake, discord.ApplicationContext):
				print("Temporary issue with NSO logins. Please try again in a minute.")
			return None
		if keys == None:
			if isinstance(snowflake, discord.ApplicationContext):
				print("Error getting token, I have logged this for my owners")
			return None

		self.__setGameKey(snowflake, game, keys)
		return keys

	def __get_session_token_mysql(self, snowflake) -> Optional[str]:
		cur = self.pynso_pool.cursor()
		cur.execute("SELECT session_token FROM tokens WHERE snowflake = %s", (str(snowflake),))
		ciphertext = cur.fetchone()
		cur.close()
		if ciphertext == None:
			return None
		else:
			return self.stringCrypt.decryptString(ciphertext[0])
			
	def __get_session_token(self, session_token_code, auth_code_verifier):
		nsoAppInfo = self.getAppVersion()
		if nsoAppInfo == None:
			print("get_session_token(): No known NSO app version")
			return None
		nsoAppVer = nsoAppInfo['version']

		head = {
			'User-Agent':      f'OnlineLounge/{nsoAppVer} NASDKAPI Android',
			'Accept-Language': 'en-US',
			'Accept':          'application/json',
			'Content-Type':    'application/x-www-form-urlencoded',
			'Host':            'accounts.nintendo.com',
			'Connection':      'Keep-Alive',
			'Accept-Encoding': 'gzip'
		}
		body = {
			'client_id':                   '71b963c1b7b6d119',
			'session_token_code':          session_token_code,
			'session_token_code_verifier': auth_code_verifier.replace(b"=", b"")
		}

		r = self.session.post('https://accounts.nintendo.com/connect/1.0.0/api/session_token', headers=head, data=body)
		if r.status_code != 200:
			print(f"ERROR IN SESSION TOKEN {r.status_code} {r.reason}: {str(r.text)}")
			return None
		else:
			return json.loads(r.text)["session_token"]

	def __callImink(self, id_token, guid, timestamp, method):
		api_app_head = {
			'Content-Type': 'application/json; charset=utf-8',
			#TODO: Make this user agent send bot owner, not my hardcoded id
			'User-Agent' : 'Jet-bot/1.0.0 (discord=jetsurf#8514)'
		}
		api_app_body = {
			'hash_method':  str(method),
			'request_id':   guid,
			'token': id_token,
			'timestamp':  str(timestamp),
		}

		r = requests.post("https://api.imink.jone.wang/f", headers=api_app_head, data=json.dumps(api_app_body))
		print(f"IMINK API RESPONSE: {r.status_code} {r.reason} {r.text}")

		if r.status_code == 500:
			print(f"Temporary issue with IMINK: {r.status_code} {r.reason} : {r.text}")
			return 500
		if r.status_code != 200:
			print(f"ERROR IN IMINK: {r.status_code} {r.reason} : {r.text}")
			return None
		else:
			return json.loads(r.text)

	def __setup_nso(self, session_token, game='s2'):
		nsoAppInfo = self.getAppVersion()
		if nsoAppInfo == None:
			print("__setup_nso(): No known NSO app version")
			return None
		nsoAppVer = nsoAppInfo['version']

		head = {
			'Host': 'accounts.nintendo.com',
			'Accept-Encoding': 'gzip',
			'Content-Type': 'application/json; charset=utf-8',
			'Accept-Language': 'en-US',
			'Accept': 'application/json',
			'Connection': 'Keep-Alive',
			'User-Agent': f'OnlineLounge/{nsoAppVer} NASDKAPI Android'
		}
		body = {
			'client_id': '71b963c1b7b6d119',
			'session_token': session_token,
			'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer-session-token'
		}

		r = requests.post("https://accounts.nintendo.com/connect/1.0.0/api/token", headers=head, json=body)
		id_response = json.loads(r.text)
		if r.status_code != 200:
			print(f"NSO ERROR IN API TOKEN {r.status_code} {r.reason}: {str(id_response)}")
			return

		head = {
			'User-Agent': f'OnlineLounge/{nsoAppVer} NASDKAPI Android',
			'Accept-Language': 'en-US',
			'Accept': 'application/json',
			'Authorization': f'Bearer {id_response["access_token"]}',
			'Host': 'api.accounts.nintendo.com',
			'Connection': 'Keep-Alive',
			'Accept-Encoding': 'gzip'
		}

		r = requests.get("https://api.accounts.nintendo.com/2.0.0/users/me", headers=head)
		user_info = json.loads(r.text)
		if r.status_code != 200:
			print(f"NSO ERROR IN USER LOGIN {r.response} {r.reason}: {str(user_info)}")
			return

		head = {
			'Host': 'api-lp1.znc.srv.nintendo.net',
			'Accept-Language': 'en-US',
			'User-Agent': f'com.nintendo.znca/{nsoAppVer} (Android/7.1.2)',
			'Accept': 'application/json',
			'X-ProductVersion': nsoAppVer,
			'Content-Type': 'application/json; charset=utf-8',
			'Connection': 'Keep-Alive',
			'Authorization': 'Bearer',
			'X-Platform': 'Android',
			'Accept-Encoding': 'gzip'
		}
		idToken = id_response["access_token"]
		timestamp = int(time.time())
		guid = str(uuid.uuid4())
		f = self.__callImink(idToken, guid, timestamp, 1)
		if f == None:
			return None
		if f == 500:
			return 500

		parameter = {
			'f':         	f["f"],
			'naIdToken':	idToken,
			'timestamp':	timestamp,
			'requestId':	guid,
			'naCountry':	user_info["country"],
			'naBirthday':	user_info["birthday"],
			'language':		user_info["language"]
		}
		body = {}
		body["parameter"] = parameter

		r = requests.post("https://api-lp1.znc.srv.nintendo.net/v3/Account/Login", headers=head, json=body)
		acnt_api = json.loads(r.text)
		if r.status_code != 200:
			print(f"NSO ERROR IN LOGIN {r.status_code} {r.reason}: {str(acnt_api)}")
			return None

		try:
			idToken = acnt_api["result"]["webApiServerCredential"]["accessToken"]
			fc = acnt_api['result']['user']['links']['friendCode']['id']
		except Exception as e:
			print(f"Account API Call failed. H: {str(acnt_api)}")
			print(f"HERES THE EXCEPTION: {str(e)}")
			return None

		if game == 'nso':
			fc = acnt_api['result']['user']['links']['friendCode']['id']
			print(f"Friend Code is: SW-{fc}")
			return { 'fc' : fc }

		timestamp = int(time.time())
		guid = str(uuid.uuid4())
		f = self.__callImink(idToken,guid, timestamp, 2)
		if f == None:
			return None
		if  f == 500:
			return 500

		head = {
			'Host': 'api-lp1.znc.srv.nintendo.net',
			'User-Agent': f'com.nintendo.znca/{nsoAppVer} (Android/7.1.2)',
			'Accept': 'application/json',
			'X-ProductVersion': nsoAppVer,
			'Content-Type': 'application/json; charset=utf-8',
			'Connection': 'Keep-Alive',
			'Authorization': f'Bearer {acnt_api["result"]["webApiServerCredential"]["accessToken"]}',
			'X-Platform': 'Android',
			'Accept-Encoding': 'gzip'
		}
		parameter = {
			'f':					f["f"],
			'registrationToken':	idToken,
			'timestamp':			timestamp,
			'requestId':			guid
		}

		if game == 'ac':
			parameter['id'] = 4953919198265344
		else:
			parameter['id'] = 5741031244955648

		body = {}
		body["parameter"] = parameter

		r = requests.post("https://api-lp1.znc.srv.nintendo.net/v2/Game/GetWebServiceToken", headers=head, json=body)
		token = json.loads(r.text)
		if r.status_code != 200:
			print(f"NSO ERROR IN GETWEBSERVICETOKEN {r.status_code} {r.reason}: {str(token)}")
			return None

		head = {
			'Host': 'placeholder',
			'X-IsAppAnalyticsOptedIn': 'false',
			'Accept': 'application/json, text/plain, */*',
			'Accept-Encoding': 'gzip, deflate, br',
			'X-GameWebToken': token["result"]["accessToken"],
			'Accept-Language': 'en-US,en;q=0.9',
			'Content-Type': 'application/json',
			'Connection': 'keep-alive',
			'DNT': '0',
			'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36',
			'X-Requested-With': 'com.nintendo.znca'
		}

		keys = {}
		if game == 'ac':
			head['Host'] = 'web.sd.lp1.acbaa.srv.nintendo.net'
			r = requests.get("https://web.sd.lp1.acbaa.srv.nintendo.net/?lang=en-US&na_country=US&na_lang=en-US", headers=head)
			if r.cookies['_gtoken'] == None:
				print(f"ERROR IN GETTING AC _GTOKEN: {str(r.text)}")
				return None
			else:
				print("Got a AC token, getting park_session")
				gtoken = r.cookies["_gtoken"]
				head = {
					'Host': 'web.sd.lp1.acbaa.srv.nintendo.net',
					'Accept': 'application/json, text/plain, */*',
					'Accept-Encoding': 'gzip, deflate, br',
					'X-Blanco-Version': '2.1.0',
					'Accept-Language': 'en-US,en;q=0.9',
					'Content-Type': 'application/json',
					'User-Agent': 'Mozilla/5.0 (Linux; Android 7.1.2; Pixel Build/NJH47D; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/59.0.3071.125 Mobile Safari/537.36',
					'Referer' : 'https://web.sd.lp1.acbaa.srv.nintendo.net/?lang=en-US&na_country=US&na_lang=en-US',
					'Origin' : ':https://web.sd.lp1.acbaa.srv.nintendo.net'
				}

				r = requests.get('https://web.sd.lp1.acbaa.srv.nintendo.net/api/sd/v1/users', headers=head, cookies=dict(_gtoken=gtoken))
				thejson = json.loads(r.text)
				if thejson['users']:
					r = requests.post("https://web.sd.lp1.acbaa.srv.nintendo.net/api/sd/v1/auth_token", headers=head, json=dict(userId=thejson['users'][0]['id']), cookies=dict(_gtoken=gtoken))
					bearer = json.loads(r.text)
					if r.cookies['_park_session'] == None or 'token' not in bearer:
						print("ERROR GETTING AC _PARK_SESSION/BEARER")
						return None
					else:
						keys = { 'gtoken' : gtoken, 'park_session' : r.cookies['_park_session'], 'ac_bearer' : bearer['token'] }
						print("Got AC _park_session and bearer!")
				else:
					return None
		else:
			head['Host'] = 'app.splatoon2.nintendo.net'
			r = requests.get("https://app.splatoon2.nintendo.net/?lang=en-US", headers=head)
			if r.status_code != 200:
				print(f"ERROR IN GETTING IKSM {r.status_code} {r.reason}: {str(r.text)}")
				return None
			else:
				print("Got a S2 token!")
				keys = { 'iksm' : r.cookies['iksm_session'] }

		return keys
