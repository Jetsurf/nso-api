import base64
import json
import time

class JWT:
	# JWT uses base64 without the usual trailing padding characters. We
	#  re-pad the string here.
	# https://www.rfc-editor.org/rfc/rfc7515#appendix-C
	@classmethod
	def pad(cls, string):
		r = len(string) % 4
		if r == 1:
			raise Exception("Malformed input")
		n = 4 - r % 4
		return string + ('=' * n)

	@classmethod
	def decode(cls, string):
		# Split into component parts
		parts = string.split('.')
		if len(parts) != 3:
			return None

		# Decode each part
		decoded = {}
		decoded['header']    = json.loads(base64.urlsafe_b64decode(cls.pad(parts[0])))
		decoded['body']      = json.loads(base64.urlsafe_b64decode(cls.pad(parts[1])))
		decoded['signature'] = base64.urlsafe_b64decode(cls.pad(parts[2]))
		return decoded

	def __init__(self, encoded):
		decoded = self.decode(encoded)
		if decoded is None:
			raise Exception("Malformed JWT")

		self.header    = decoded['header']
		self.body      = decoded['body']
		self.signature = decoded['signature']

	def remainingTime(self):
		if self.body.get('exp'):
			return max(0, self.body['exp'] - time.time())

		return None

	def expiryTime(self):
		return self.body.get('exp')
