#!/usr/bin/env python3

import json
import os.path
import sys

from nso_api.nso_api import NSO_API
from nso_api.imink import IMink

# Utility function to load JSON from a file
def load_json_file(filename):
	if not os.path.exists(filename):
		return None
	with open(filename, 'r') as f:
		return json.load(f)

# Utility function to save JSON to a file
def save_json_file(filename, keys):
	with open(filename, 'w') as f:
		json.dump(keys, f)

# The NSO client object will trigger this callback when the tokens change.
def handle_keys_update(nso, context):
	save_json_file("nso_tokens.json", nso.get_keys())

# The NSO client object will trigger this callback when it detects that the
#  account is logged out.
def handle_logged_out(nso, context):
	print(f"Client for context '{context}' was logged out.")

# This function loads our existing tokens (if any) from the file and performs
#  the setup process if needed.
def load_tokens(nso):
	keys = load_json_file("nso_tokens.json")
	if keys:
		nso.set_keys(keys)

	if not nso.is_logged_in():
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

def showUsageMessage():
	print(f"Usage: {sys.argv[0]} <category> <command>")
	print(f"       {sys.argv[0]} <category> --help")
	print("Categories are: account s2 s3")
	return

def grabArguments(args, min, max, names):
		if len(args) < min:
			print(f"Too few args, got {len(args)} but expected at least {min}")
		elif len(args) > max:
			print(f"Too many args, got {len(args)} but expected at most {max}")
		else:
			data = {}
			for a in range(len(args)):
				data[names[a]] = args[a]
			return data

		arglist = " ".join([ f"<{n}>" for n in names])
		print(f"Usage: {sys.argv[0]} {sys.argv[1]} {sys.argv[2]} {arglist}")
		exit(1)

def accountCommand(words):
	command = words.pop(0)
	if command == 'get-user-by-friend-code':
		args = grabArguments(words, 1, 1, ['friendcode'])
		print(json.dumps(nso.account.get_user_by_friend_code(args['friendcode'])))
	elif command == 'add-friend-by-friend-code':
		args = grabArguments(words, 1, 1, ['friendcode'])
		user = nso.account.get_user_by_friend_code(args['friendcode'])
		if user is None:
			print("Couldn't retrieve user with that friend code.")
			return

		print(json.dumps(nso.account.send_friend_request(user)))
	elif command == '--help':
		print("Subcommands of 'account' are:")
		print("  get-user-by-friend-code <code>")
		print("  add-friend-by-friend-code <code>")
	else:
		print(f"Unknown account command '{command}'. Try '--help' for help.")

def s2Command(words):
	command = words.pop(0)
	if command == 'get-ranks':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s2.get_ranks()))
	elif command == '--help':
		print("Subcommands of 's2' are:")
		print("  get-ranks")
	else:
		print(f"Unknown s2 command '{command}'. Try '--help' for help.")

def s3Command(words):
	command = words.pop(0)
	if command == 'get-web-app-version':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_web_app_version()))
	elif command == 'get-web-app-image-links':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_web_app_image_links()))
	elif command == 'extract-web-app-embedded-images':
		args = grabArguments(words, 0, 0, [])
		images = nso.s3.extract_web_app_embedded_images()
		print("%-64s  %-6s  %s" % ('sha256', 'length', 'mimetype'))
		for i in images:
			print("%s  %6d  %s" % (i['sha256'], len(i['data']), i['mimetype']))
	elif command == 'get-splatfest-list':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_splatfest_list()))
	elif command == 'get-salmon-run-stats':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_salmon_run_stats()))
	elif command == 'get-stage-schedule':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_stage_schedule()))
	elif command == 'get-store-items':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_store_items()))
	elif command == 'get-player-stats-full':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_player_stats_full()))
	elif command == 'get-battle-history-list':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_battle_history_list()))
	elif command == 'get-battle-history-details':
		args = grabArguments(words, 1, 1, ['battlenum'])
		list = nso.s3.get_battle_history_list()
		if list is None:
			print("Failed to get battle history list")
			return

		battles = list['data']['latestBattleHistories']['historyGroups']['nodes'][0]['historyDetails']['nodes']
		if len(battles) == 0:
			print("No battles in history list")
			return

		if (int(args['battlenum']) < 0) or (int(args['battlenum']) >= len(battles)):
			print(f"Requested battle {args['battlenum']} but there are only entries 0 through {len(battles) - 1}")
			return

		details = nso.s3.get_battle_history_detail(battles[int(args['battlenum'])]['id'])
		print(json.dumps(details))
	elif command == 'get-salmon-run-history-list':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_sr_history_list()))
	elif command == 'get-salmon-run-history-details':
		args = grabArguments(words, 1, 1, ['shiftnum'])
		list = nso.s3.get_sr_history_list()
		if list is None:
			print("Failed to get salmon run history list")
			return

		# The response has shifts grouped by rotation. Here we gather a linear list of shifts.
		groups = list['data']['coopResult']['historyGroups']['nodes']
		shifts = []
		for g in groups:
			for s in g['historyDetails']['nodes']:
				shifts.append(s)

		if len(shifts) == 0:
			print("No shifts in history list")
			return

		if (int(args['shiftnum']) < 0) or (int(args['shiftnum']) >= len(shifts)):
			print(f"Requested shift {args['shiftnum']} but there are only entries 0 through {len(shifts) - 1}")
			return

		shift = shifts[int(args['shiftnum'])]
		details = nso.s3.get_sr_history_detail(shift['id'])
		print(json.dumps(details))
	elif command == 'get-outfits':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_outfits()))
	elif command == 'get-outfits-common-data':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_outfits_common_data()))
	elif command == 'get-replay-list':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_replay_list()))
	elif command == 'export-gear-seed-file':
		args = grabArguments(words, 0, 0, [])
		if not (data := nso.s3.get_gear_seed_data()):
			print("Could not get gear seed data")
			return

		filename = f"gear_{data['timestamp']}.json"
		with open(filename, "w") as f:
			json.dump(data, f)

		print(f"Exported to: {filename}")
	elif command == '--help':
		print("Subcommands of 's3' are:")
		print("  get-web-app-version")
		print("  get-web-app-image-links")
		print("  extract-web-app-images")
		print("  get-splatfest-list")
		print("  get-salmon-run-stats")
		print("  get-stage-schedule")
		print("  get-store-items")
		print("  get-player-stats-full")
		print("  get-battle-history-list")
		print("  get-battle-history-details <battlenum>")
		print("  get-salmon-run-history-list")
		print("  get-salmon-run-history-details <shiftnum>")
		print("  get-outfits")
		print("  get-outfits-common-data")
		print("  get-replay-list")
		print("  export-gear-seed-file")
	else:
		print(f"Unknown s3 command '{command}'. Try '--help' for help.")

imink = IMink("nso-cli.py 1.0 (discord=jetsurf#8514)")
nso_app_version = "2.4.0"

# Create NSO client object
nso = NSO_API(nso_app_version, imink)
nso.on_keys_update(handle_keys_update)
nso.on_logged_out(handle_logged_out)

# Load tokens into client object
load_tokens(nso)

if not nso.is_logged_in():
	print("Not logged in. Can't continue.")
	exit(1)

if len(sys.argv) < 3:
	showUsageMessage()
	exit(1)

category = sys.argv[1]
if category == 'account':
	accountCommand(sys.argv[2:])
elif category == 's2':
	s2Command(sys.argv[2:])
elif category == 's3':
	s3Command(sys.argv[2:])
elif category == '--help':
	showUsageMessage()
	exit(1)
else:
	print(f"Unknown category '{category}'. Try '--help' for help.")
	exit(1)

# Print any error messages
if nso.has_error():
	print(f"Error: {nso.get_error_message()}")

