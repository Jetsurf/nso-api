#!/usr/bin/env python3

import json
import os.path
import sys

from nso_api.nso_api import NSO_API
from nso_api.imink import IMink
from nso_api.nxapi import NXApi #For NXAPI use, only 1 f-provider is needed

def load_json_file(filename):
	if not os.path.exists(filename):
		return None
	with open(filename, 'r') as f:
		return json.load(f)

def save_json_file(filename, data):
	with open(filename, 'w') as f:
		json.dump(data, f)

def handle_user_data_update(nso, context):
	print(f"User data updated for context '{context}'. Saving...")
	save_json_file("nso_tokens.json", nso.get_user_data())

def handle_global_data_update(data):
	print(f"Global data updated. Saving...")
	save_json_file("nso_global_data.json", data)

def handle_logged_out(nso, context):
	print(f"Client for context '{context}' was logged out.")

imink = IMink(f"nso-cli.py {NSO_API.get_version()} (discord=jetsurf)")
#nsapi = NXApi(f"nso-cli.py {NSO_API.get_version()} (discord=jetsurf)") ## For NXApi use instead

# Context is a value of your choice that will be provided to callbacks. If you
#  create multiple client objects, you can use it to tell them apart. If you
#  don't, its value does not matter.
context = 123

nso = NSO_API(imink, context)
#nso.app_version_override = "2.7.1"
nso.on_user_data_update(handle_user_data_update)
nso.on_global_data_update(handle_global_data_update)
nso.on_logged_out(handle_logged_out)

nso.load_global_data(load_json_file("nso_global_data.json"))

keys = load_json_file("nso_tokens.json")
if keys:
	print("I have saved keys, skipping login")
	nso.load_user_data(keys)
else:
	url = nso.get_login_challenge_url()
	print(f"Login challenge URL: {url}")
	user_input = ""
	while not "://" in user_input:
		print("Paste login URL here:")
		user_input = input().rstrip()
	if not nso.complete_login_challenge(user_input):
		print(f"Login failed: {nso.get_error_message()}")
		exit(1)

	print("Login successful")

ranks = nso.s2.get_ranks()
if ranks is not None:
	print(ranks)
else:
	print(nso.get_error_message())
