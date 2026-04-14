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
    cc.crypted_color   = ConfigText(default="#FF3232", fixed_size=False)  # Red   - encrypted, no NCam
    cc.decrypted_color = ConfigText(default="#00C800", fixed_size=False)  # Green - decrypted via NCam
    cc.fta_color       = ConfigText(default="#FFFFFF", fixed_size=False)  # White - free-to-air
    cc.enabled         = ConfigSelection(
        choices=[("yes", _("Yes")), ("no", _("No"))],
        default="yes"
    )


class ChannelColorsSetup(Screen, ConfigListScreen):
    skin = """
        <screen name="ChannelColorsSetup" position="center,center" size="600,420"
                title="Channel Colors Settings">
            <widget name="config" position="10,10" size="580,360"
                    scrollbarMode="showOnDemand" />
            <widget name="key_red"   position="0,380"   size="150,40"
                    valign="center" halign="center"
                    backgroundColor="#9f1313" font="Regular;18"
                    foregroundColor="#ffffff" />
            <widget name="key_green" position="150,380" size="150,40"
                    valign="center" halign="center"
                    backgroundColor="#1f771f" font="Regular;18"
                    foregroundColor="#ffffff" />
            <widget name="key_yellow" position="300,380" size="200,40"
                    valign="center" halign="center"
                    backgroundColor="#7a7a00" font="Regular;18"
                    foregroundColor="#ffffff" />
        </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.title = _("Channel Colors Settings")
        ConfigListScreen.__init__(
            self,
            [
                getConfigListEntry(_("Plugin Enabled"),                    cc.enabled),
                getConfigListEntry(_("Encrypted Color (Red)"),             cc.crypted_color),
                getConfigListEntry(_("NCam Decryptable Color (Green)"),    cc.decrypted_color),
                getConfigListEntry(_("Free-to-Air Color (White)"),         cc.fta_color),
            ],
            session
        )
        self["key_red"]    = Button(_("Cancel"))
        self["key_green"]  = Button(_("Save"))
        self["key_yellow"] = Button(_("Reload NCam"))
        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "green":  self.save,
                "red":    self.cancel,
                "yellow": self.reload_ncam,
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

    def reload_ncam(self):
        """Force reload NCam CAID list from disk."""
        try:
            from .ColorApplier import reload_ncam_caids
            caids = reload_ncam_caids()
            from Screens.MessageBox import MessageBox
            self.session.open(
                MessageBox,
                _("NCam CAID list reloaded: %d entries") % len(caids),
                MessageBox.TYPE_INFO,
                timeout=3
            )
        except Exception as e:
            pass
