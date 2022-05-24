import time

class NSO_Expiring_Token:
	def __init__(self, value, duration = None, expiretime = None):
		self.value = value
		self.createtime = int(time.time())
		if duration != None:
			self.duration = duration
		elif expiretime:
			self.duration = expiretime - self.createtime
		else:
			raise Exception("No expiry time?")

	# Given a hash, constructs an instance
	@classmethod
	def from_hash(cls, hash):
		token = cls(hash['value'], 0)
		token.createtime = hash['createtime']
		token.duration   = hash['duration']
		return token

	# Returns the token as a hash
	def to_hash(self):
		return {'value': self.value, 'createtime': self.createtime, 'duration': self.duration}

	# Returns the value of the token if not expired, otherwise None.
	def get_value(self):
		if self.is_expired():
			return None
		return self.value

	# Returns true if token is fresh (less than 90% expired)
	def is_fresh(self):
		now = time.time()
		return now < (self.createtime + self.duration * 0.90)

	# Returns true if token is stale (>90% expired but <100% expired)
	def is_stale(self):
		now = time.time()
		return (now > (self.createtime + self.duration * 0.90)) and (now < (self.createtime + self.duration))

	# Returns true if token is expired
	def is_expired(self):
		now = time.time()
		return now > (self.createtime + self.duration)

