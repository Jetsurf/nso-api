from bs4 import BeautifulSoup
import requests
import re

class GooglePlay():
	def getAppVersion(self, packageName):
		params = {'id': packageName, 'hl' : 'en_US'}
		headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0'}
		response = requests.get('https://play.google.com/store/apps/details', params = params, headers = headers)
		if response.status_code != requests.codes.ok:
			print(f"getAppVersion(): Retrieving '{response.url}' got status code {response.status_code}")
			return None

		soup = BeautifulSoup(response.text, 'html5lib')
		label = soup.find(self.filterVersionLabelElement)
		if label == None:
			print(f"getAppVersion(): Cannot find version label")
			return None

		version = label.find_next_sibling().string
		if version == None:
			print(f"getAppVersion(): Cannot find version string")
			return None

		if not re.fullmatch(r'^[0-9]+([.][0-9]+)*', version):
			print(f"getAppVersion(): Rejecting strange-looking version string '{version}'")
			return None

		return version

	def filterVersionLabelElement(self, tag):
		return (tag.name == 'div') and (tag.string == "Current Version")
