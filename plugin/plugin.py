# -*- coding: utf-8 -*-
#
# plugin.py
# Enigma 2 Channel Colors Plugin — Entry Point
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
    patch_service_list()

    desc = PluginDescriptor(
        name="Channel Colors",
        description="Colorize channels by encryption state",
        where=PluginDescriptor.WHERE_PLUGINMENU,
        fnc=main,
    )
    return [desc]
