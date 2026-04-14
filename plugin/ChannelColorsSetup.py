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
from .ColorApplier import VERSION


if not hasattr(config, 'plugins'):
    from Components.config import ConfigSubsection as _CS
    config.plugins = _CS()

if not hasattr(config.plugins, 'channelcolors'):
    config.plugins.channelcolors = ConfigSubsection()

cc = config.plugins.channelcolors
if not hasattr(cc, 'enabled'):
    cc.enabled         = ConfigSelection(
        choices=[("yes", _("Yes")), ("no", _("No"))],
        default="yes"
    )
    cc.crypted_color   = ConfigText(default="#FF3232", fixed_size=False)
    cc.decrypted_color = ConfigText(default="#00C800", fixed_size=False)
    cc.fta_color       = ConfigText(default="#FFFFFF", fixed_size=False)


class ChannelColorsSetup(Screen, ConfigListScreen):
    skin = """
        <screen name="ChannelColorsSetup" position="center,center" size="640,460"
                title="Channel Colors Settings">
            <widget name="config" position="10,10" size="620,380"
                    scrollbarMode="showOnDemand" />
            <widget name="key_red"    position="0,420"   size="160,40"
                    valign="center" halign="center"
                    backgroundColor="#9f1313" font="Regular;18"
                    foregroundColor="#ffffff" />
            <widget name="key_green"  position="160,420" size="160,40"
                    valign="center" halign="center"
                    backgroundColor="#1f771f" font="Regular;18"
                    foregroundColor="#ffffff" />
            <widget name="key_yellow" position="320,420" size="200,40"
                    valign="center" halign="center"
                    backgroundColor="#7a7a00" font="Regular;18"
                    foregroundColor="#ffffff" />
            <widget name="key_blue"   position="520,420" size="120,40"
                    valign="center" halign="center"
                    backgroundColor="#18188b" font="Regular;18"
                    foregroundColor="#ffffff" />
        </screen>
    """

    def __init__(self, session):
        Screen.__init__(self, session)
        self.title = _("Channel Colors v%s") % VERSION
        ConfigListScreen.__init__(
            self,
            [
                getConfigListEntry(_("Plugin Enabled"),                cc.enabled),
                getConfigListEntry(_("Encrypted color (no NCam)"),     cc.crypted_color),
                getConfigListEntry(_("Decryptable color (NCam+FTA)"),  cc.decrypted_color),
            ],
            session
        )
        self["key_red"]    = Button(_("Cancel"))
        self["key_green"]  = Button(_("Save"))
        self["key_yellow"] = Button(_("Reload NCam"))
        self["key_blue"]   = Button(_("v%s") % VERSION)
        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "green":  self.save,
                "red":    self.cancel,
                "yellow": self.reload_ncam,
                "blue":   self.show_info,
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
        try:
            from .ColorApplier import reload_ncam_caids, _ncam_caids, _lamedb_caids
            caids = reload_ncam_caids()
            ldb   = _lamedb_caids or {}
            from Screens.MessageBox import MessageBox
            self.session.open(
                MessageBox,
                _("Reloaded: NCam=%d CAIDs | lamedb=%d services") % (len(caids), len(ldb)),
                MessageBox.TYPE_INFO,
                timeout=4
            )
        except Exception as e:
            pass

    def show_info(self):
        try:
            from .ColorApplier import get_ncam_caids, get_lamedb_caids
            ncam  = get_ncam_caids()
            ldb   = get_lamedb_caids()
            from Screens.MessageBox import MessageBox
            self.session.open(
                MessageBox,
                _("Channel Colors v%s\nNCam CAIDs: %d\nlamedb services: %d\n\nRed=Encrypted | Green=NCam+FTA | Gray=No signal") % (
                    VERSION, len(ncam), len(ldb)),
                MessageBox.TYPE_INFO,
                timeout=6
            )
        except Exception as e:
            pass
