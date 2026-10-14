"""Where the homelab plugins keep their files.

The plugins share the bot's volume. 5.x maps it at /app/config and 4.x at
/app/schedule; the same choice store.py makes, kept separate so that
homelab/docker_updates.py --scan, which runs on its own, does not have to initialise
the bot's storage to find its files.
"""
import os
import pathlib

CONFIG_ROOT = "/app/config"
LEGACY_ROOT = "/app/schedule"


def data_dir():
	if os.environ.get("HOMELAB_DATA_DIR"):
		return pathlib.Path(os.environ["HOMELAB_DATA_DIR"])
	return pathlib.Path(CONFIG_ROOT if os.path.isdir(CONFIG_ROOT) else LEGACY_ROOT)


def data_file(name):
	return data_dir() / name


def certificate(path):
	"""The Portainer certificate: the configured path, else a copy in the volume.

	The image no longer carries it, so that this public repository does not.
	"""
	if path and os.path.isfile(path):
		return path
	return str(data_file(os.path.basename(path or "portainer-cert.pem")))
