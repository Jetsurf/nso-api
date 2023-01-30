import itunes_app_scraper.scraper

class NSO_API_App:
	ITUNES_APP_ID = 1234806557

	def __init__(self, nso_api):
		self.nso_api = nso_api

	def get_version(self):
		scraper = itunes_app_scraper.scraper.AppStoreScraper()
		nso_app_info = scraper.get_app_details(self.ITUNES_APP_ID, country = 'us')
		if nso_app_info and (version := nso_app_info.get('version')):
			return version

		return None
