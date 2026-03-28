# -*- coding: utf-8 -*-
# ChannelColorsSetup.py - Settings screen for Channel Colors plugin
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


# Initialize config subsection
if not hasattr(config, 'plugins'):
    from Components.config import ConfigSubsection as _CS
    config.plugins = _CS()

if not hasattr(config.plugins, 'channelcolors'):
    config.plugins.channelcolors = ConfigSubsection()

cc = config.plugins.channelcolors
if not hasattr(cc, 'crypted_color'):
    cc.crypted_color   = ConfigText(default="#FF3232", fixed_size=False)  # Red    - encrypted
    cc.decrypted_color = ConfigText(default="#FFD700", fixed_size=False)  # Gold   - decrypted via NCam
    cc.fta_color       = ConfigText(default="#00C800", fixed_size=False)  # Green  - free-to-air
    cc.enabled         = ConfigSelection(
        choices=[("yes", _("Yes")), ("no", _("No"))],
        default="yes"
    )


class ChannelColorsSetup(Screen, ConfigListScreen):
    skin = """
        <screen name="ChannelColorsSetup" position="center,center" size="600,400"
                title="Channel Colors Settings">
            <widget name="config" position="10,10" size="580,320"
                    scrollbarMode="showOnDemand" />
            <widget name="key_red"   position="0,360"   size="150,40"
                    valign="center" halign="center"
                    backgroundColor="#9f1313" font="Regular;18"
                    foregroundColor="#ffffff" />
            <widget name="key_green" position="150,360" size="150,40"
                    valign="center" halign="center"
                    backgroundColor="#1f771f" font="Regular;18"
                    foregroundColor="#ffffff" />
        </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.title = _("Channel Colors Settings")
        ConfigListScreen.__init__(
            self,
            [
                getConfigListEntry(_("Plugin Enabled"),            cc.enabled),
                getConfigListEntry(_("Encrypted Channel Color"),   cc.crypted_color),
                getConfigListEntry(_("Decrypted Channel Color"),   cc.decrypted_color),
                getConfigListEntry(_("Free-to-Air Channel Color"), cc.fta_color),
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
        for entry in self["config"].list:
            entry[1].save()
        configfile.save()
        self.close(True)

    def cancel(self):
        for entry in self["config"].list:
            entry[1].cancel()
        self.close(False)
