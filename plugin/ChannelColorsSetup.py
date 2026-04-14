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


RAW_BASE = "https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/plugin"
INSTALL_DIR = "/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
FILES = ["__init__.py", "plugin.py", "ColorApplier.py", "ChannelColorsSetup.py"]


def _open_url(url, timeout=10):
    try:
        import urllib2
        r = urllib2.urlopen(url, timeout=timeout)
        d = r.read()
        r.close()
        return d
    except ImportError:
        pass
    try:
        import urllib.request
        r = urllib.request.urlopen(url, timeout=timeout)
        d = r.read()
        r.close()
        return d
    except Exception as e:
        raise e


def _get_remote_version():
    import re
    data = _open_url(RAW_BASE + '/ColorApplier.py')
    if isinstance(data, bytes):
        data = data.decode('utf-8', errors='replace')
    m = re.search(r"^VERSION\s*=\s*'([0-9]+\.[0-9]+\.[0-9]+)'", data, re.MULTILINE)
    if m:
        return m.group(1)
    return None


def _do_update():
    import os
    os.makedirs(INSTALL_DIR, exist_ok=True)
    for fname in FILES:
        data = _open_url(RAW_BASE + '/' + fname)
        path = os.path.join(INSTALL_DIR, fname)
        with open(path, 'wb') as f:
            f.write(data if isinstance(data, bytes) else data.encode('utf-8'))
    # read new version
    import re
    with open(os.path.join(INSTALL_DIR, 'ColorApplier.py'), 'r') as f:
        content = f.read()
    m = re.search(r"^VERSION\s*=\s*'([0-9]+\.[0-9]+\.[0-9]+)'", content, re.MULTILINE)
    return m.group(1) if m else '?'


class ChannelColorsSetup(Screen, ConfigListScreen):
    skin = """
        <screen name="ChannelColorsSetup" position="center,center" size="640,500"
                title="Channel Colors Settings">
            <widget name="config" position="10,10" size="620,400"
                    scrollbarMode="showOnDemand" />
            <widget name="key_red"    position="0,460"   size="160,40"
                    valign="center" halign="center"
                    backgroundColor="#9f1313" font="Regular;18"
                    foregroundColor="#ffffff" />
            <widget name="key_green"  position="160,460" size="160,40"
                    valign="center" halign="center"
                    backgroundColor="#1f771f" font="Regular;18"
                    foregroundColor="#ffffff" />
            <widget name="key_yellow" position="320,460" size="160,40"
                    valign="center" halign="center"
                    backgroundColor="#7a7a00" font="Regular;18"
                    foregroundColor="#ffffff" />
            <widget name="key_blue"   position="480,460" size="160,40"
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
                getConfigListEntry(_("Plugin Enabled"),               cc.enabled),
                getConfigListEntry(_("Encrypted color (no NCam)"),    cc.crypted_color),
                getConfigListEntry(_("Decryptable color (NCam)"),     cc.decrypted_color),
                getConfigListEntry(_("FTA color"),                    cc.fta_color),
            ],
            session
        )
        self["key_red"]    = Button(_("Cancel"))
        self["key_green"]  = Button(_("Save"))
        self["key_yellow"] = Button(_("Reload"))
        self["key_blue"]   = Button(_("Update"))
        self["actions"] = ActionMap(
            ["SetupActions", "ColorActions"],
            {
                "green":  self.save,
                "red":    self.cancel,
                "yellow": self.reload_ncam,
                "blue":   self.check_update,
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
            from .ColorApplier import reload_ncam_caids, _lamedb_caids
            caids = reload_ncam_caids()
            ldb   = _lamedb_caids or {}
            from Screens.MessageBox import MessageBox
            self.session.open(
                MessageBox,
                _("Reloaded\nNCam CAIDs : %d\nlamedb     : %d services") % (len(caids), len(ldb)),
                MessageBox.TYPE_INFO,
                timeout=4
            )
        except Exception as e:
            self._msg(_("Reload failed: %s") % str(e), error=True)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def check_update(self):
        from Screens.MessageBox import MessageBox
        self.session.openWithCallback(
            self._do_check,
            MessageBox,
            _("Checking for updates...\nCurrent version: v%s") % VERSION,
            MessageBox.TYPE_INFO,
            timeout=2
        )

    def _do_check(self, _=None):
        from Screens.MessageBox import MessageBox
        try:
            remote = _get_remote_version()
        except Exception as e:
            self.session.open(
                MessageBox,
                _("Cannot reach GitHub:\n%s") % str(e),
                MessageBox.TYPE_ERROR,
                timeout=5
            )
            return

        if remote is None:
            self.session.open(
                MessageBox,
                _("Could not read remote version."),
                MessageBox.TYPE_ERROR,
                timeout=4
            )
            return

        if remote == VERSION:
            self.session.open(
                MessageBox,
                _("Already up to date!\nInstalled: v%s\nRemote   : v%s") % (VERSION, remote),
                MessageBox.TYPE_INFO,
                timeout=5
            )
        else:
            self.session.openWithCallback(
                self._confirm_update,
                MessageBox,
                _("Update available!\nInstalled : v%s\nNew       : v%s\n\nInstall now?") % (VERSION, remote),
                MessageBox.TYPE_YESNO
            )

    def _confirm_update(self, confirmed):
        if not confirmed:
            return
        from Screens.MessageBox import MessageBox
        # show progress
        self.session.openWithCallback(
            self._run_update,
            MessageBox,
            _("Downloading update...\nPlease wait."),
            MessageBox.TYPE_INFO,
            timeout=2
        )

    def _run_update(self, _=None):
        from Screens.MessageBox import MessageBox
        try:
            new_ver = _do_update()
            self.session.openWithCallback(
                self._restart_prompt,
                MessageBox,
                _("Update installed!\nNew version: v%s\n\nRestart enigma2 now?") % new_ver,
                MessageBox.TYPE_YESNO
            )
        except Exception as e:
            self.session.open(
                MessageBox,
                _("Update failed:\n%s") % str(e),
                MessageBox.TYPE_ERROR,
                timeout=6
            )

    def _restart_prompt(self, restart):
        if restart:
            import os
            os.system('init 4 && sleep 2 && init 3 &')
            self.close(False)

    def _msg(self, text, error=False):
        from Screens.MessageBox import MessageBox
        self.session.open(
            MessageBox,
            text,
            MessageBox.TYPE_ERROR if error else MessageBox.TYPE_INFO,
            timeout=5
        )
