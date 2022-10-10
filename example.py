#!/usr/bin/env python3

import json
import os.path
import sys

from nso_api.nso_api import NSO_API
from nso_api.imink import IMink

def load_keys(filename):
	if not os.path.exists(filename):
		return None
	with open(filename, 'r') as f:
		return json.load(f)

def save_keys(filename, keys):
	with open(filename, 'w') as f:
		json.dump(keys, f)

def handle_keys_update(nso, context):
	print(f"Keys updated for context '{context}'. Saving...")
	save_keys("nso_tokens.json", nso.get_keys())

def handle_logged_out(nso, context):
	print(f"Client for context '{context}' was logged out.")

imink = IMink("nso_api 1.0/example (discord=jetsurf#8514)")
nso_app_version = "2.3.1"

# Context is a value of your choice that will be provided to callbacks. If you
#  create multiple client objects, you can use it to tell them apart. If you
#  don't, its value does not matter.
context = 123

nso = NSO_API(nso_app_version, imink, context)
nso.on_keys_update(handle_keys_update)
nso.on_logged_out(handle_logged_out)

keys = load_keys("nso_tokens.json")
if keys:
	print("I have saved keys, skipping login")
	nso.set_keys(keys)
else:
	url = nso.get_login_challenge_url()
	print(f"Login challenge URL: {url}")
	input = ""
	while not "://" in input:
		print("Paste login URL here:")
		input = sys.stdin.readline().rstrip()
	if not nso.complete_login_challenge(input):
		print(f"Login failed: {nso.get_error_message()}")
		exit(1)

	print("Login successful")

ranks = nso.s2.get_ranks()
if ranks is not None:
	print(ranks)
else:
	print(nso.get_error_message())
