"""
Homelab plugins on top of the upstream bot.

Run on its own (python3 tests/test_homelab.py) so that tests/run_all.py, an
upstream file, stays untouched. It loads the bot exactly as the upstream tests
do and checks the things a new upstream release could quietly break: that the
plugin handlers still win over the core's catch-alls, that /status, /quota and
the update buttons reach the plugins, that the command menu carries them, and
that only administrators get through.
"""
import json
import os
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness
sys.path.insert(0, harness.REPO)

harness.load_bot()
os.environ["HOMELAB_DATA_DIR"] = harness.tempdir()
from homelab import plugins as homelab_plugins  # noqa: E402
from homelab import paths as homelab_paths  # noqa: E402

core = sys.modules["core"]
bot = core.bot


def message(text, uid=4405089, chat_type="private", chat_id=None):
	import telebot
	entities = [{"type": "bot_command", "offset": 0, "length": len(text.split()[0])}] if text.startswith("/") else []
	return telebot.types.Message.de_json({
		"message_id": 1, "date": 0, "text": text, "entities": entities,
		"chat": {"id": chat_id if chat_id is not None else uid, "type": chat_type},
		"from": {"id": uid, "is_bot": False, "first_name": "test"},
	})


def first_message_handler(msg):
	for handler in bot.message_handlers:
		if bot._test_message_handler(handler, msg):
			return handler["function"]
	return None


def first_callback_handler(data):
	call = types.SimpleNamespace(data=data)
	for handler in bot.callback_query_handlers:
		if all(test(call) for name, test in handler["filters"].items() if name == "func"):
			return handler["function"]
	return None


def test_plugin_commands_win_over_the_core():
	assert first_message_handler(message("/status")).__module__ == "homelab.n8n_status"
	assert first_message_handler(message("/quota")).__module__ == "homelab.quota_status"
	# The core still answers its own commands and the catch-all stays last.
	assert first_message_handler(message("/list")).__module__ == "core"
	assert bot.message_handlers[-1]["function"].__module__ == "core"


def test_update_buttons_reach_docker_updates():
	assert first_callback_handler("du:approve:x").__module__ == "homelab.docker_updates"
	assert first_callback_handler("something-else").__module__ == "core"


def test_command_menu_lists_the_plugins_first():
	import telebot
	merged = homelab_plugins.merge_commands([telebot.types.BotCommand("/start", "x"),
											telebot.types.BotCommand("/status", "duplicate")])
	assert [c.command for c in merged] == ["/status", "/quota", "/start"]
	assert getattr(bot.set_my_commands, "__name__", "") == "<lambda>"


def test_only_administrators_are_allowed():
	menu = homelab_plugins.menu
	assert menu.allowed(message("/quota"), 4405089)
	# 440508 is a prefix of the admin id: a substring check would let it in.
	assert not menu.allowed(message("/quota", uid=440508), 440508)
	# An admin writing from a group that is not TELEGRAM_GROUP is ignored.
	assert not menu.allowed(message("/quota", chat_type="group", chat_id=-100123), 4405089)


def test_quota_reads_the_status_file_from_the_volume():
	path = homelab_paths.data_file("account-watch/status.json")
	path.parent.mkdir(parents=True, exist_ok=True)
	import time
	path.write_text(json.dumps({"generated_at": time.time(), "report": "📊 test report"}))
	sent = []
	original = bot.send_message
	bot.send_message = lambda chat, text, **kw: sent.append(text)
	try:
		first_message_handler(message("/quota"))(message("/quota"))
	finally:
		bot.send_message = original
	assert sent == ["📊 test report"], sent


def test_certificate_falls_back_to_the_volume():
	assert homelab_paths.certificate("/nonexistent/portainer-cert.pem") == str(homelab_paths.data_file("portainer-cert.pem"))


if __name__ == "__main__":
	failed = 0
	for name, fn in sorted(globals().items()):
		if name.startswith("test_") and callable(fn):
			try:
				fn()
				print(f"ok    {name}")
			except Exception as ex:
				failed += 1
				print(f"FAIL  {name}: {type(ex).__name__}: {ex}")
	sys.exit(1 if failed else 0)
