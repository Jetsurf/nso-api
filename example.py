import json
import os.path
import sys

from pynso.nso_api import NSO_API
from pynso.imink import IMink

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
	save_keys("nso_keys.json", nso.get_keys())

imink = IMink("pynso 1.0/example (discord=jetsurf#8514)")
nso_app_version = "2.2.0"

nso = NSO_API(nso_app_version, imink, 123) #123 here is a snowflake, useful for combining with other services
nso.on_keys_update(handle_keys_update)

keys = load_keys("nso_keys.json")
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

print(nso.s2.get_ranks())
