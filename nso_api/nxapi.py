from .imink import IMink

class NXApi(IMink):
	PREFIX_URL = "https://nxapi-znca-api.fancy.org.uk/api/znca"
	PROJECT_URL = "https://github.com/samuelthomas2774/nxapi-znca-api"

	def __init__(self, user_agent, prefix_url = PREFIX_URL):
		super().__init__(user_agent, prefix_url)