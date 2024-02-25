import itunes_app_scraper.scraper

class NSO_API_App:
	ITUNES_APP_ID = 1234806557

	def __init__(self, nso_api, f_provider):
		self.nso_api = nso_api
		self.f_provider = f_provider

	def get_version(self):
		#Exception for if this function isn't implemented/unsupported by f-provider?
		ver = self.f_provider.get_supported_app_ver()
		print(f"Using f-provider nso-app ver {ver}")
		return ver
		#print("f-provider supported app version not supported")

		scraper = itunes_app_scraper.scraper.AppStoreScraper()
		nso_app_info = scraper.get_app_details(self.ITUNES_APP_ID, country = 'us')
		if nso_app_info and (version := nso_app_info.get('version')):
			return version

		return None
