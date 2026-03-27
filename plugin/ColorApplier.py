# -*- coding: utf-8 -*-
#
# ColorApplier.py - Final working implementation for OpenATV 7.x
#
# eListboxServiceContent (sl.l) does NOT support per-row foreground color.
# It uses global named color slots (serviceNotAvail, serviceStreamed, etc.)
# and a crypto icon mode for CA state visualization.
#
# Our approach:
#   1. Hook ChannelSelectionBase.__init__ to get the live servicelist instance
#   2. On onShow, apply our color scheme to the named color slots:
#      - servicePseudoRecorded  -> crypted_color   (encrypted channels)
#      - serviceStreamed         -> decrypted_color (NCam-decrypted channels)
#      - serviceNotAvail        -> fta_color        (FTA channels)
#   3. Set setCryptoIconMode(1) to enable crypto-based row coloring
#   4. Call setRoot again to force a redraw with new colors
#
# This is the same approach used by OpenATV's built-in skin color system.
#
# Author: Ossama Hashim (SamoTech)
# License: MIT

from Components.config import config
import os

try:
    from enigma import iServiceInformation, gRGB, eServiceReference
except ImportError:
    iServiceInformation = None
    gRGB = None
    eServiceReference = None


def _parse_color(hex_str):
    """Convert '#RRGGBB' to gRGB."""
    try:
        h = hex_str.strip().lstrip('#')
        return gRGB(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except Exception:
        return None


def _apply_colors(sl):
    """
    Apply channel colors to a ServiceListLegacy instance (sl).
    sl.l is eListboxServiceContent.
    """
    try:
        if config.plugins.channelcolors.enabled.value != "yes":
            return
        if gRGB is None:
            return

        l = sl.l
        fta_color       = _parse_color(config.plugins.channelcolors.fta_color.value)
        crypted_color   = _parse_color(config.plugins.channelcolors.crypted_color.value)
        decrypted_color = _parse_color(config.plugins.channelcolors.decrypted_color.value)

        # eListboxServiceContent named color slots:
        # serviceNotAvail      = service not available / scrambled (encrypted)
        # servicePseudoRecorded = pseudo-state, repurpose for decrypted
        # serviceStreamed      = streaming state, repurpose for FTA
        # Standard foreground  = index 0 via setColor()

        # Map our colors to the crypto-state slots
        # slot 0 = normal foreground (FTA)
        # slot 1 = serviceNotAvail   (encrypted/scrambled)
        # slot 2 = foreground selected
        # slot 3 = background selected

        # Use setColor for standard slots
        if fta_color:
            l.setColor(0, fta_color)        # normal foreground -> FTA

        # Named slots for crypto states
        if crypted_color and hasattr(l, 'serviceNotAvail'):
            l.serviceNotAvail(crypted_color)    # scrambled = not available

        if decrypted_color and hasattr(l, 'servicePseudoRecorded'):
            l.servicePseudoRecorded(decrypted_color)  # decrypted by NCam

        # Enable crypto-based coloring mode
        # Mode 0 = off, 1 = use crypto icons, 2 = color by crypto state
        if hasattr(l, 'setCryptoIconMode'):
            l.setCryptoIconMode(2)

        # Force list redraw
        root = sl.getRoot()
        if root and hasattr(sl, 'setRoot'):
            sl.setRoot(root)

    except Exception as e:
        print("[ChannelColors] _apply_colors error: %s" % str(e))


def patch_service_list():
    print("[ChannelColors] patch_service_list called")

    try:
        from Screens.ChannelSelection import ChannelSelectionBase
    except ImportError as e:
        print("[ChannelColors] Cannot import ChannelSelectionBase: %s" % str(e))
        return

    if getattr(ChannelSelectionBase, '_cc_patched', False):
        return

    orig_init = ChannelSelectionBase.__init__

    def _patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        try:
            sl = self.servicelist
            # Apply colors immediately
            _apply_colors(sl)
            # Re-apply whenever channel list is shown (bouquet switch etc.)
            if hasattr(self, 'onShow'):
                self.onShow.append(lambda: _apply_colors(self.servicelist))
        except Exception as e:
            print("[ChannelColors] init hook error: %s" % str(e))

    ChannelSelectionBase.__init__ = _patched_init
    ChannelSelectionBase._cc_patched = True
    print("[ChannelColors] ChannelSelectionBase patched OK")
