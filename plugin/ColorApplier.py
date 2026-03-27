# -*- coding: utf-8 -*-
#
# ColorApplier.py
# Patches Enigma2's ServiceList to colorize channel entries
# based on encryption/decryption state.
#
# Strategy:
#   - Monkey-patch ServiceList.buildEntry to inject foreground
#     color into each list row via eListboxPythonMultiContent.
#   - CA state is read from iServiceInformation:
#       sIsCrypted   == 0  → Free-to-air
#       sIsCrypted   == 1
#         sIsScrambled == 1  → Encrypted (NCam not decrypting)
#         sIsScrambled == 0  → Decrypted (NCam active CW)
#
# Author: Ossama Hashim (SamoTech)
# License: MIT

from Components.config import config

try:
    from enigma import iServiceInformation, eServiceReference, gRGB
except ImportError:
    iServiceInformation = None
    gRGB = None


def _parse_color(hex_str):
    """Convert '#RRGGBB' to gRGB object, or None on error."""
    try:
        h = hex_str.strip().lstrip('#')
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return gRGB(r, g, b)
    except Exception:
        return None


def _get_ca_color(service_ref):
    """
    Returns gRGB color for service based on CA state, or None.
    """
    if config.plugins.channelcolors.enabled.value != "yes":
        return None
    if iServiceInformation is None or gRGB is None:
        return None
    try:
        info = service_ref.info()
        if info is None:
            return None
        is_crypted = info.getInfo(iServiceInformation.sIsCrypted)
        if is_crypted != 1:
            return _parse_color(config.plugins.channelcolors.fta_color.value)
        is_scrambled = info.getInfo(iServiceInformation.sIsScrambled)
        if is_scrambled == 0:
            return _parse_color(config.plugins.channelcolors.decrypted_color.value)
        else:
            return _parse_color(config.plugins.channelcolors.crypted_color.value)
    except Exception as e:
        print("[ChannelColors] _get_ca_color error: %s" % str(e))
        return None


def patch_service_list():
    """
    Patches ServiceList.buildEntry to inject per-row foreground
    color based on CA state. Called once at plugin startup.
    """
    try:
        from Components.ServiceList import ServiceList
    except ImportError:
        print("[ChannelColors] Cannot import ServiceList")
        return

    if getattr(ServiceList, '_cc_patched', False):
        return

    original_buildEntry = ServiceList.buildEntry

    def _patched_buildEntry(self, service):
        # Call original builder first
        original_buildEntry(self, service)

        # Now override foreground color for this entry
        try:
            color = _get_ca_color(service)
            if color is not None:
                # eListboxPythonMultiContent foreground color index:
                # setForegroundColor sets it for current item being built
                self.l.setForegroundColor(color)
        except Exception as e:
            print("[ChannelColors] _patched_buildEntry error: %s" % str(e))

    ServiceList.buildEntry = _patched_buildEntry
    ServiceList._cc_patched = True
    print("[ChannelColors] ServiceList.buildEntry patched successfully")
