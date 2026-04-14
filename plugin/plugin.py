# -*- coding: utf-8 -*-
# plugin.py - Enigma2 Channel Colors Plugin Entry Point
# Author: Ossama Hashim (SamoTech)
# License: MIT

from Plugins.Plugin import PluginDescriptor
from .ChannelColorsSetup import ChannelColorsSetup
from .ColorApplier import patch_service_list, VERSION


def main(session, **kwargs):
    session.open(ChannelColorsSetup)


def Plugins(**kwargs):
    patch_service_list()
    return [
        PluginDescriptor(
            name="Channel Colors v%s" % VERSION,
            description="Red=Encrypted | Green=NCam/FTA | Gray=No Signal",
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main,
        )
    ]
