# -*- coding: utf-8 -*-
#
# plugin.py
# Enigma 2 Channel Colors Plugin — Entry Point
#
# Registers plugin in the Plugins menu and applies the ServiceList
# color patch at startup so channel colors are live immediately.
#
# Compatible with:
#   - OpenATV (openatv/enigma2)
#   - NCam emulator (fairbird/NCam) via DVB-API
#   - Fury-FHD skin (islam-2412/IPKS)
#
# Author: Ossama Hashim (SamoTech)
# License: MIT

from Plugins.Plugin import PluginDescriptor
from .ChannelColorsSetup import ChannelColorsSetup
from .ColorApplier import patch_service_list
import os


def main(session, **kwargs):
    session.open(ChannelColorsSetup)


def Plugins(**kwargs):
    # Apply the ServiceList color patch once at Enigma2 startup
    patch_service_list()

    # Resolve icon path safely
    _icon = os.path.join(os.path.dirname(__file__), "icon.png")
    icon_arg = "icon.png" if os.path.isfile(_icon) else None

    desc = PluginDescriptor(
        name="Channel Colors",
        description="Configure encrypted/decrypted channel colors",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        fnc=main,
    )
    if icon_arg:
        desc.icon = icon_arg

    return [desc]
