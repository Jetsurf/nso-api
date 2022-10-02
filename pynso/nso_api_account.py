import re

class NSO_API_Account:
	def __init__(self, nso_api):
		self.nso_api = nso_api
		self.cache = {}

	def format_friend_code(self, friend_code):
		match = re.match("^(?:SW-)?([0-9]{4})[- ]?([0-9]{4})[- ]?([0-9]{4})$", friend_code)
		if not match:
			return None
		return f"{match[1]}-{match[2]}-{match[3]}"

	def list_web_services(self):
		response = self.nso_api.do_znc_call("/v1/Game/ListWebServices", {})
		if self.nso_api.record_response_error(response):
			return None

		return response.result()

	def get_announcements(self):
		response = self.nso_api.do_znc_call("/v1/Announcement/List", {})
		if self.nso_api.record_response_error(response):
			return None

		return response.result()

	def get_friends_list(self):
		response = self.nso_api.do_znc_call("/v3/Friend/List", {})
		if self.nso_api.record_response_error(response):
			return None

		return response.result()

	def create_friend_code_url(self):
		response = self.nso_api.do_znc_call("/v3/Friend/CreateFriendCodeUrl", {})
		if self.nso_api.record_response_error(response):
			return None

		return response.result()

	def get_user_self(self):
		response = self.nso_api.do_znc_call("/v3/User/ShowSelf", {})
		if self.nso_api.record_response_error(response):
			return None

		return response.result()

	def get_user_by_friend_code(self, friend_code):
		friend_code = self.format_friend_code(friend_code)
		if not friend_code:
			raise Exception("get_user_by_friend_code(): Malformed friend code string")

		response = self.nso_api.do_znc_call("/v3/Friend/GetUserByFriendCode", {'friendCode': friend_code})
		if self.nso_api.record_response_error(response):
			return None

		return response.result()

	# Nintendo returns an empty object (dictionary) on success.
	def send_friend_request(self, user):
		if not user.get("nsaId"):
			raise Exception("send_friend_request(): No nsaId for user")

		response = self.nso_api.do_znc_call("/v3/FriendRequest/Create", {'nsaId': user['nsaId']})
		if self.nso_api.record_response_error(response):
			return None

		return response.result()
