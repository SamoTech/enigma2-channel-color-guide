# -*- coding: utf-8 -*-
#
# ChannelColorsSetup.py
# Settings screen for the Channel Colors plugin
#
# Author: Ossama Hashim (SamoTech)
# License: MIT

from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.config import (
    config, ConfigSubsection, ConfigText,
    ConfigSelection, getConfigListEntry, configfile
)
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Button import Button


# ── Default config values ────────────────────────────────────────────────────
if not hasattr(config.plugins, 'channelcolors'):
    config.plugins.channelcolors = ConfigSubsection()

if not hasattr(config.plugins.channelcolors, 'crypted_color'):
    config.plugins.channelcolors.crypted_color   = ConfigText(default="#FF0000", fixed_size=False)  # Red   – encrypted
    config.plugins.channelcolors.decrypted_color = ConfigText(default="#FFD700", fixed_size=False)  # Gold  – decrypted (NCam active)
    config.plugins.channelcolors.fta_color       = ConfigText(default="#FFFFFF", fixed_size=False)  # White – free-to-air
    config.plugins.channelcolors.enabled         = ConfigSelection(
        choices=[("yes", _("Yes")), ("no", _("No"))],
        default="yes"
    )


class ChannelColorsSetup(Screen, ConfigListScreen):
    """
    GUI settings screen for Channel Colors plugin.
    Allows user to set colours for:
      - Encrypted (locked) channels          → crypted_color
      - Decrypted (active NCam/OSCam share)  → decrypted_color
      - Free-to-air channels                 → fta_color

    Compatible with:
      - OpenATV 7.0+ / OpenPLi 9.0+
      - NCam (fairbird/NCam) via DVB-API
      - Fury-FHD skin (islam-2412/IPKS)
    """

    skin = """
        <screen name="ChannelColorsSetup" position="center,center" size="600,400" title="Channel Colors Settings">
            <widget name="config" position="10,10" size="580,320" scrollbarMode="showOnDemand" />
            <widget name="key_red"   position="0,360"   size="150,40" valign="center" halign="center"
                    backgroundColor="#9f1313" font="Regular;18" foregroundColor="#ffffff" />
            <widget name="key_green" position="150,360" size="150,40" valign="center" halign="center"
                    backgroundColor="#1f771f" font="Regular;18" foregroundColor="#ffffff" />
        </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.title = _("Channel Colors Settings")

        ConfigListScreen.__init__(
            self,
            [
                getConfigListEntry(_("Plugin Enabled"),            config.plugins.channelcolors.enabled),
                getConfigListEntry(_("Encrypted Channel Color"),   config.plugins.channelcolors.crypted_color),
                getConfigListEntry(_("Decrypted Channel Color"),   config.plugins.channelcolors.decrypted_color),
                getConfigListEntry(_("Free-to-Air Channel Color"), config.plugins.channelcolors.fta_color),
            ],
            session
        )

        self["key_red"]   = Button(_("Cancel"))
        self["key_green"] = Button(_("Save"))

        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "green":  self.save,
                "red":    self.cancel,
                "save":   self.save,
                "cancel": self.cancel,
                "ok":     self.save,
            },
            -2
        )

    def save(self):
        """Persist settings via Enigma2 config system and close."""
        for entry in self["config"].list:
            entry[1].save()
        configfile.save()
        self.close(True)

    def cancel(self):
        """Discard changes."""
        for entry in self["config"].list:
            entry[1].cancel()
        self.close(False)
