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
    config, ConfigSubsection, ConfigColor,
    ConfigSelection, getConfigListEntry, configfile
)
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Button import Button


# ── Default config values ────────────────────────────────────────────────────
config.plugins.channelcolors = ConfigSubsection()
config.plugins.channelcolors.crypted_color = ConfigColor(default="#FF0000")       # Red  – encrypted
config.plugins.channelcolors.decrypted_color = ConfigColor(default="#FFD700")     # Gold – decrypted
config.plugins.channelcolors.fta_color = ConfigColor(default="#FFFFFF")           # White – free-to-air
config.plugins.channelcolors.enabled = ConfigSelection(
    choices=[("yes", _("Yes")), ("no", _("No"))],
    default="yes"
)


class ChannelColorsSetup(Screen, ConfigListScreen):
    """
    GUI settings screen for Channel Colors plugin.
    Allows user to set colours for:
      - Encrypted (locked) channels
      - Decrypted (unlocked via sharing server) channels
      - Free-to-air channels
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

        # Build config list entries
        self["config"] = ConfigListScreen.__init__(
            self,
            [
                getConfigListEntry(_("Plugin Enabled"),          config.plugins.channelcolors.enabled),
                getConfigListEntry(_("Encrypted Channel Color"),  config.plugins.channelcolors.crypted_color),
                getConfigListEntry(_("Decrypted Channel Color"),  config.plugins.channelcolors.decrypted_color),
                getConfigListEntry(_("Free-to-Air Channel Color"), config.plugins.channelcolors.fta_color),
            ],
            session
        )

        self["key_red"]   = Button(_("Cancel"))
        self["key_green"] = Button(_("Save"))

        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "green": self.save,
                "red":   self.cancel,
                "save":  self.save,
                "cancel": self.cancel,
                "ok":    self.save,
            },
            -2
        )

    def save(self):
        """Persist settings and apply colors."""
        for entry in self["config"].list:
            entry[1].save()
        configfile.save()
        self._apply_colors()
        self.close(True)

    def cancel(self):
        """Discard changes."""
        for entry in self["config"].list:
            entry[1].cancel()
        self.close(False)

    def _apply_colors(self):
        """
        Write color values to the Enigma 2 settings file so they
        are picked up by the channel list widget on next GUI restart.
        """
        settings_path = "/etc/enigma2/settings"
        keys = {
            "config.plugins.channelcolors.crypted_color":   config.plugins.channelcolors.crypted_color.value,
            "config.plugins.channelcolors.decrypted_color": config.plugins.channelcolors.decrypted_color.value,
            "config.plugins.channelcolors.fta_color":       config.plugins.channelcolors.fta_color.value,
        }
        try:
            with open(settings_path, "r") as f:
                lines = f.readlines()

            existing = {line.split("=")[0]: line for line in lines if "=" in line}
            for k, v in keys.items():
                existing[k] = f"{k}={v}\n"

            with open(settings_path, "w") as f:
                f.writelines(existing.values())
        except Exception as e:
            print(f"[ChannelColors] Error writing settings: {e}")
