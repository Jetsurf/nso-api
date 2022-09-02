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
		return self.nso_api.do_znc_call("/v1/Game/ListWebServices", {})

	def get_announcements(self):
		return self.nso_api.do_znc_call("/v1/Announcement/List", {})

	def get_friends_list(self):
		return self.nso_api.do_znc_call("/v3/Friend/List", {})

	def create_friend_code_url(self):
		return self.nso_api.do_znc_call("/v3/Friend/CreateFriendCodeUrl", {})

	def get_user_self(self):
		result = self.nso_api.do_znc_call("/v3/User/ShowSelf", {})
		if not result:
			return
		elif result.get('status') != 0:
			self.nso_api.errors.append(f"Bad status from ShowSelf: {result.get('status')} {result.get('errorMessage')}")
			return

		return result.get('result')

	def get_user_by_friend_code(self, friend_code):
		friend_code = self.format_friend_code(friend_code)
		if not friend_code:
			raise Exception("get_user_by_friend_code(): Malformed friend code string")

		result = self.nso_api.do_znc_call("/v3/Friend/GetUserByFriendCode", {'friendCode': friend_code})
		if not result:
			return
		elif result.get('status') != 0:
			self.nso_api.errors.append(f"Bad status from GetUserByFriendCode: {result.get('status')} {result.get('errorMessage')}")
			return

		return result.get('result')

	def send_friend_request(self, user):
		if not user.get("nsaId"):
			raise Exception("send_friend_request(): No nsaId for user")

		return self.nso_api.do_znc_call("/v3/FriendRequest/Create", {'nsaId': user['nsaId']})
