# -*- coding: utf-8 -*-
# ChannelColorsSetup.py - Settings screen for Channel Colors plugin v1.9.2
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


RAW_BASE    = "https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/plugin"
INSTALL_DIR = "/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
FILES       = ["__init__.py", "plugin.py", "ColorApplier.py", "ChannelColorsSetup.py"]


def _open_url(url, timeout=10):
    try:
        import urllib2
        r = urllib2.urlopen(url, timeout=timeout)
        d = r.read()
        r.close()
        return d
    except ImportError:
        pass
    import urllib.request
    r = urllib.request.urlopen(url, timeout=timeout)
    d = r.read()
    r.close()
    return d


def _get_remote_version():
    import re
    data = _open_url(RAW_BASE + '/ColorApplier.py')
    if isinstance(data, bytes):
        data = data.decode('utf-8', errors='replace')
    m = re.search(r"^VERSION\s*=\s*'([0-9]+\.[0-9]+\.[0-9]+)'", data, re.MULTILINE)
    return m.group(1) if m else None


def _do_update():
    import os, re
    os.makedirs(INSTALL_DIR, exist_ok=True)
    for fname in FILES:
        data = _open_url(RAW_BASE + '/' + fname)
        path = os.path.join(INSTALL_DIR, fname)
        with open(path, 'wb') as f:
            f.write(data if isinstance(data, bytes) else data.encode('utf-8'))
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
        self._update_thread = None

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
            self._msg(_("Reloaded\nNCam CAIDs : %d\nlamedb     : %d services") % (len(caids), len(ldb)))
        except Exception as e:
            self._msg(_("Reload failed: %s") % str(e), error=True)

    # ------------------------------------------------------------------
    # Update - runs in background thread, posts result via enigma2 timer
    # ------------------------------------------------------------------
    def check_update(self):
        if self._update_thread and self._update_thread.is_alive():
            self._msg(_("Update check already running..."))
            return

        self._msg(_("Checking for update...\nCurrent: v%s") % VERSION)

        import threading
        self._thread_result = None
        self._thread_error  = None

        def _worker():
            try:
                self._thread_result = _get_remote_version()
            except Exception as e:
                self._thread_error = str(e)

        self._update_thread = threading.Thread(target=_worker)
        self._update_thread.daemon = True
        self._update_thread.start()

        # poll every 500ms until thread done
        self._poll_check()

    def _poll_check(self):
        from enigma import eTimer
        if not hasattr(self, '_check_timer'):
            self._check_timer = eTimer()
            self._check_timer.callback.append(self._on_check_timer)
        self._check_timer.start(500, True)

    def _on_check_timer(self):
        if self._update_thread and self._update_thread.is_alive():
            # still running - poll again
            self._check_timer.start(500, True)
            return

        from Screens.MessageBox import MessageBox

        if self._thread_error:
            self._msg(_("Cannot reach GitHub:\n%s") % self._thread_error, error=True)
            return

        remote = self._thread_result
        if remote is None:
            self._msg(_("Could not read remote version."), error=True)
            return

        if remote == VERSION:
            self._msg(_("Already up to date!\nInstalled: v%s\nRemote   : v%s") % (VERSION, remote))
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
        self._msg(_("Downloading v%s...\nPlease wait.") % self._thread_result)

        import threading
        self._install_error  = None
        self._install_result = None

        def _install_worker():
            try:
                self._install_result = _do_update()
            except Exception as e:
                self._install_error = str(e)

        t = threading.Thread(target=_install_worker)
        t.daemon = True
        t.start()
        self._install_thread = t
        self._poll_install()

    def _poll_install(self):
        if not hasattr(self, '_install_timer'):
            from enigma import eTimer
            self._install_timer = eTimer()
            self._install_timer.callback.append(self._on_install_timer)
        self._install_timer.start(500, True)

    def _on_install_timer(self):
        if self._install_thread and self._install_thread.is_alive():
            self._install_timer.start(500, True)
            return

        if self._install_error:
            self._msg(_("Update failed:\n%s") % self._install_error, error=True)
            return

        from Screens.MessageBox import MessageBox
        self.session.openWithCallback(
            self._restart_prompt,
            MessageBox,
            _("Update installed! v%s\nRestart enigma2 now?") % self._install_result,
            MessageBox.TYPE_YESNO
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
