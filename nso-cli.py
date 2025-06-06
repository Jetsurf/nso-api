#!/usr/bin/env python3

import json
import os.path
import sys

from nso_api.nso_api import NSO_API
from nso_api.nxapi import NXApi

opts = {}
opts["user_data_file"] = "nso_tokens.json"
opts["global_data_file"] = "nso_global_data.json"

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
def handle_user_data_update(nso, context):
	save_json_file(opts["user_data_file"], nso.get_user_data())

def handle_global_data_update(data):
	save_json_file(opts["global_data_file"], data)

# The NSO client object will trigger this callback when it detects that the
#  account is logged out.
def handle_logged_out(nso, context):
	print(f"Client for context '{context}' was logged out.")

# This function loads our existing tokens (if any) from the token file.
def load_tokens(nso):
	keys = load_json_file(opts["user_data_file"])
	if keys:
		nso.load_user_data(keys)

def load_global_data(nso):
	data = load_json_file(opts["global_data_file"])
	if data:
		nso.load_global_data(data)

def showUsageMessage():
	print(f"Usage: {sys.argv[0]} [options] <category> <command>")
	print(f"       {sys.argv[0]} [options] <category> --help")
	print(f"       {sys.argv[0]} [options] --login")
	print("Categories are: app account s2 s3 acnh")
	print("Options are:")
	print("  --user-data-file <filename>   Use the given file for user-specific token data (default 'nso_tokens.json')")
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

def appCommand(words):
	command = words.pop(0)
	if command == 'get-version':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.app.get_version()))
	elif command == '--help':
		print("Subcommands of 'app' are:")
		print("  get-version")
	else:
		print(f"Unknown app command '{command}'. Try '--help' for help.")

def accountCommand(words):
	command = words.pop(0)
	if command == 'list-web-services':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.account.list_web_services()))
	elif command == 'get-friends-list':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.account.get_friends_list()))
	elif command == 'create-friend-code-url':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.account.create_friend_code_url()))
	elif command == 'get-user-self':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.account.get_user_self()))
	elif command == 'get-user-by-friend-code':
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
		print("  list-web-services")
		print("  get-friends-list")
		print("  create-friend-code-url")
		print("  get-user-self")
		print("  get-user-by-friend-code <code>")
		print("  add-friend-by-friend-code <code>")
	else:
		print(f"Unknown account command '{command}'. Try '--help' for help.")

def s2Command(words):
	command = words.pop(0)
	if command == 'get-ranks':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s2.get_ranks()))
	elif command == 'get-store-merchandise':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s2.get_store_merchandise()))
	elif command == '--help':
		print("Subcommands of 's2' are:")
		print("  get-ranks")
		print("  get-store-merchandise")
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
		args = grabArguments(words, 0, 1, ['directory'])
		images = nso.s3.extract_web_app_embedded_images()
		print("%-64s  %-6s  %s" % ('sha256', 'length', 'mimetype'))
		for i in images:
			print("%s  %6d  %s" % (i['sha256'], len(i['data']), i['mimetype']))

		extensions = {'image/png': '.png', 'image/jpeg': '.jpeg', 'image/svg+xml': '.svg'}
		if args.get('directory'):
			for i in images:
				path = f"{args['directory']}/{i['sha256']}{extensions.get(i['mimetype'], '')}"
				with open(path, 'wb') as f:
					f.write(i['data'])
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
	elif command == 'get-tw-history-list':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.s3.get_tw_history_list()))
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
		print("  extract-web-app-embedded-images [<destination directory>]")
		print("  get-splatfest-list")
		print("  get-salmon-run-stats")
		print("  get-stage-schedule")
		print("  get-store-items")
		print("  get-player-stats-full")
		print("  get-battle-history-list")
		print("  get-battle-history-details <battlenum>")
		print("  get-tw-history-list")
		print("  get-salmon-run-history-list")
		print("  get-salmon-run-history-details <shiftnum>")
		print("  get-outfits")
		print("  get-outfits-common-data")
		print("  get-replay-list")
		print("  export-gear-seed-file")
	else:
		print(f"Unknown s3 command '{command}'. Try '--help' for help.")

def acnhCommand(words):
	command = words.pop(0)
	if command == 'get-emotes':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.acnh.get_emotes()))
	elif command == 'get-catalog-items-latest':
		args = grabArguments(words, 0, 0, [])
		print(json.dumps(nso.acnh.get_catalog_items_latest()))
	elif command == '--help':
		print("Subcommands of 'acnh' are:")
		print("  get-emotes")
		print("  get-catalog-items-latest")
	else:
		print(f"Unknown acnh command '{command}'. Try '--help' for help.")

nxapi = NXApi(f"nso-cli.py {NSO_API.get_version()} (discord=jetsurf)")

# Create NSO client object
nso = NSO_API(nxapi)
nso.on_user_data_update(handle_user_data_update)
nso.on_global_data_update(handle_global_data_update)
nso.on_logged_out(handle_logged_out)

# Option args
args = sys.argv[1:]
while len(args) and args[0][0:2] == "--":
	if args[0] == "--user-data-file":
		args.pop(0)
		opts["user_data_file"] = args.pop(0)
	elif args[0] == "--override-app-version":
		args.pop(0)
		opts["override_app_version"] = args.pop(0)
	elif args[0] == "--login":
		args.pop(0)
		opts["login"] = True
	elif args[0] == "--expire-keys":
		args.pop(0)
		opts["expire_keys"] = True
	elif args[0] == "--version":
		print(f"NSO-API version: {nso.get_version()}")
		exit(0)
	else:
		print("Unknown option argument!")
		showUsageMessage()
		exit(1)

# Load tokens into client object
load_tokens(nso)
load_global_data(nso)

# Override app version if requested
if "override_app_version" in opts:
	nso.override_app_version(opts["override_app_version"])

# Options that can't be used with other commands
if opts.get("login"):
	url = nso.get_login_challenge_url()
	print(f"Login challenge URL: {url}")
	user_input = ""
	while not "://" in user_input:
		print("Paste login URL here:")
		user_input = input().rstrip()

	if nso.complete_login_challenge(user_input):
		print("Login OK")
		exit(0)
	else:
		print(f"Login failed: {nso.get_error_message()}")
		exit(1)
elif opts.get("expire_keys"):
		nso.expire_keys()
		print("Expired keys.")
		exit(0)

# Can't continue if not logged in
if not nso.is_logged_in():
	print(f"You are not logged in. Try: {sys.argv[0]} --login")
	exit(1)

if len(args) < 2:
	showUsageMessage()
	exit(1)

category = args[0]
if category == 'app':
	appCommand(args[1:])
elif category == 'account':
	accountCommand(args[1:])
elif category == 's2':
	s2Command(args[1:])
elif category == 's3':
	s3Command(args[1:])
elif category == 'acnh':
  acnhCommand(args[1:])
elif category == '--help':
	showUsageMessage()
	exit(1)
else:
	print(f"Unknown category '{category}'. Try '--help' for help.")
	exit(1)

# Print any error messages
if nso.has_error():
	print(f"Error: {nso.get_error_message()}")

