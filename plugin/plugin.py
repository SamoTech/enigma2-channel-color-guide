# -*- coding: utf-8 -*-
#
# Enigma 2 Channel Colors Plugin
# Adds a GUI to configure encrypted/decrypted channel list colors
#
# Author: Ossama Hashim (SamoTech)
# License: MIT

from Plugins.Plugin import PluginDescriptor
from .ChannelColorsSetup import ChannelColorsSetup


def main(session, **kwargs):
    session.open(ChannelColorsSetup)


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name="Channel Colors",
            description="Configure encrypted/decrypted channel colors",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            icon="icon.png",
            fnc=main,
        )
    ]
