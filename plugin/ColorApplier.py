# -*- coding: utf-8 -*-
#
# ColorApplier.py - Patches ServiceList to colorize channels by CA state
# Author: Ossama Hashim (SamoTech)
# License: MIT
#
# CA state logic:
#   sIsCrypted == 0              -> Free-to-air  -> fta_color
#   sIsCrypted == 1
#     sIsScrambled == 1          -> Encrypted    -> crypted_color
#     sIsScrambled == 0          -> Decrypted    -> decrypted_color

from Components.config import config

try:
    from enigma import iServiceInformation, gRGB
except ImportError:
    iServiceInformation = None
    gRGB = None


def _parse_color(hex_str):
    """Convert '#RRGGBB' string to gRGB object."""
    try:
        h = hex_str.strip().lstrip('#')
        return gRGB(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except Exception:
        return None


def _get_ca_color(service_ref):
    """Return gRGB color for service based on CA state, or None."""
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
        print("[ChannelColors] _get_ca_color error: %s" % str(e))
        return None


def patch_service_list():
    """Monkey-patch ServiceList.buildEntry to inject per-row foreground color."""
    try:
        from Components.ServiceList import ServiceList
    except ImportError:
        print("[ChannelColors] Cannot import ServiceList")
        return

    if getattr(ServiceList, '_cc_patched', False):
        return

    original_buildEntry = ServiceList.buildEntry

    def _patched_buildEntry(self, service):
        original_buildEntry(self, service)
        try:
            color = _get_ca_color(service)
            if color is not None:
                self.l.setForegroundColor(color)
        except Exception as e:
            print("[ChannelColors] buildEntry error: %s" % str(e))

    ServiceList.buildEntry = _patched_buildEntry
    ServiceList._cc_patched = True
    print("[ChannelColors] ServiceList.buildEntry patched OK")
