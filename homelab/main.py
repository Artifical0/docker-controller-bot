#!/usr/bin/env python3
"""
Entry point of the homelab image (python3 homelab/main.py).

Loads the upstream entry point as a module, which imports everything that
registers commands and callbacks without starting the bot, then installs the
homelab plugins and starts the bot. Following the upstream entry point instead
of copying its imports means a new upstream registrar is picked up without
touching this file, and leaves every upstream file unmodified.
"""
import importlib.util
import os

import sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP)
os.chdir(APP)
spec = importlib.util.spec_from_file_location("upstream_entry", os.path.join(APP, "docker-controller-bot.py"))
spec.loader.exec_module(importlib.util.module_from_spec(spec))

import core  # noqa: E402
from homelab import plugins  # noqa: E402,F401  (/status, /quota and the Portainer update flow)

if __name__ == "__main__":
	core.main()
