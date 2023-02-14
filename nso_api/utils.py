#!/usr/bin/python3
import base64

# Murmurhash3 (https://en.wikipedia.org/wiki/MurmurHash#Algorithm)
def murmurhash3_32(bytes, seed):
	c1 = 0xcc9e2d51
	c2 = 0x1b873593
	n = 0xe6546b64

	hash = seed

	length = len(bytes)

	# Walk through the input in 32-bit chunks
	for i in range(int(length / 4)):
		k = (bytes[i * 4 + 3] << 24) | (bytes[i * 4 + 2] << 16) | (bytes[i * 4 + 1] << 8) | bytes[i * 4]

		k = (k * c1) & 0xFFFFFFFF
		k = ((k << 15) & 0xFFFFFFFF) | (k >> 17)  # ROL 15
		k = (k * c2) & 0xFFFFFFFF

		hash = hash ^ k
		hash = ((hash << 13) & 0xFFFFFFFF) | (hash >> 19)  # ROL 13
		hash = ((hash * 5) + n) & 0xFFFFFFFF

	# Read the remaining 0-3 bytes into a final 32-bit chunk
	k = 0
	for i in range(length % 4):
		k <<= 8
		byte = bytes[length - i - 1]
		k |= byte

	# Process the final chunk
	k = (k * c1) & 0xFFFFFFFF
	k = ((k << 15) & 0xFFFFFFFF) | (k >> 17)  # ROL 15
	k = (k * c2) & 0xFFFFFFFF
	hash = hash ^ k

	# Generate final value
	hash ^= length
	hash ^= (hash >> 16)
	hash = (hash * 0x85ebca6b) & 0xFFFFFFFF
	hash ^= (hash >> 13)
	hash = (hash * 0xc2b2ae35) & 0xFFFFFFFF
	hash ^= (hash >> 16)

	return hash

# Base64 encoding with no trailing padding
def base64_encode_no_pad(data):
	return base64.urlsafe_b64encode(data).rstrip(b"=")
