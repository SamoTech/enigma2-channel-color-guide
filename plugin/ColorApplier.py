# -*- coding: utf-8 -*-
#
# ColorApplier.py
# OpenATV 7.x: ServiceList is created at startup inside ChannelSelectionBase.
# We hook ChannelSelectionBase.__init__ to get the live instance, then
# patch its onSelectionChanged to recolor on every cursor move,
# and its onShow to recolor when the list becomes visible.
#
# Author: Ossama Hashim (SamoTech)
# License: MIT

from Components.config import config
import os

try:
    from enigma import iServiceInformation, gRGB
except ImportError:
    iServiceInformation = None
    gRGB = None

DEBUG_LOG = "/tmp/cc_debug.log"


def _log(msg):
    print("[ChannelColors] " + msg)
    try:
        with open(DEBUG_LOG, 'a') as f:
            f.write("[ChannelColors] " + msg + "\n")
    except Exception:
        pass


def _parse_color(hex_str):
    try:
        h = hex_str.strip().lstrip('#')
        return gRGB(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except Exception as e:
        _log("_parse_color error '%s': %s" % (hex_str, str(e)))
        return None


def _get_ca_color(service_ref):
    try:
        if config.plugins.channelcolors.enabled.value != "yes":
            return None
        if iServiceInformation is None or gRGB is None:
            return None
        info = service_ref.info()
        if info is None:
            return None
        is_crypted = info.getInfo(iServiceInformation.sIsCrypted)
        if is_crypted != 1:
            return _parse_color(config.plugins.channelcolors.fta_color.value)
        is_scrambled = info.getInfo(iServiceInformation.sIsScrambled)
        if is_scrambled == 0:
            return _parse_color(config.plugins.channelcolors.decrypted_color.value)
        return _parse_color(config.plugins.channelcolors.crypted_color.value)
    except Exception as e:
        _log("_get_ca_color error: %s" % str(e))
        return None


def _recolor_list(channel_selection):
    """
    Called on show/selectionChanged - recolors all visible items.
    """
    try:
        sl = channel_selection.servicelist
        _log("_recolor_list: sl type=%s" % type(sl))
        _log("_recolor_list: sl methods=%s" % [m for m in dir(sl) if not m.startswith('__')])

        # Try to get the root service list and iterate
        if hasattr(sl, 'getList'):
            items = sl.getList()
            _log("getList type=%s" % type(items))
            if items is not None:
                _log("getList len=%d" % len(items))
        if hasattr(sl, 'list'):
            _log("sl.list type=%s" % type(sl.list))
        if hasattr(sl, 'l'):
            l = sl.l
            _log("sl.l type=%s" % type(l))
            _log("sl.l methods=%s" % [m for m in dir(l) if not m.startswith('__')])
    except Exception as e:
        _log("_recolor_list error: %s" % str(e))


def patch_service_list():
    try:
        os.remove(DEBUG_LOG)
    except Exception:
        pass

    _log("patch_service_list called")

    try:
        from Screens.ChannelSelection import ChannelSelectionBase
    except ImportError as e:
        _log("Cannot import ChannelSelectionBase: %s" % str(e))
        return

    if getattr(ChannelSelectionBase, '_cc_patched', False):
        _log("Already patched")
        return

    orig_init = ChannelSelectionBase.__init__

    def _patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        _log("ChannelSelectionBase.__init__ called")
        try:
            # Log what attributes are available
            _log("self attrs: %s" % [a for a in dir(self) if 'service' in a.lower() or 'list' in a.lower()])

            # Hook onShow to recolor when channel list opens
            if hasattr(self, 'onShow'):
                self.onShow.append(lambda: _recolor_list(self))
                _log("onShow hook added")

            # Hook onSelectionChanged if available
            if hasattr(self, 'onSelectionChanged'):
                self.onSelectionChanged.append(lambda: _recolor_list(self))
                _log("onSelectionChanged hook added")
        except Exception as e:
            _log("__init__ patch error: %s" % str(e))

    ChannelSelectionBase.__init__ = _patched_init
    ChannelSelectionBase._cc_patched = True
    _log("ChannelSelectionBase.__init__ patched - restart Enigma2 and open channel list")
