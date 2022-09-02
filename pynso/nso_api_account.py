class NSO_API_Account:
	def __init__(self, nso_api):
		self.nso_api = nso_api
		self.cache = {}

	def list_web_services(self):
		return self.nso_api.do_znc_call("/v1/Game/ListWebServices", {})

	def get_announcements(self):
		return self.nso_api.do_znc_call("/v1/Announcement/List", {})

	def get_friends_list(self):
		return self.nso_api.do_znc_call("/v3/Friend/List", {})

	def create_friend_code_url(self):
		return self.nso_api.do_znc_call("/v3/Friend/CreateFriendCodeUrl", {})

	def get_user_info(self):
		return self.nso_api.do_znc_call("/v3/User/ShowSelf", {})
