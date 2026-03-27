# -*- coding: utf-8 -*-
#
# ColorApplier.py
# Detects channel encryption/decryption state and returns the
# correct foreground color for the Enigma 2 ServiceList renderer.
#
# CA detection strategy (compatible with NCam / fairbird/NCam via DVB-API):
#   iServiceInformation.sIsCrypted   → 1 if channel has CA descriptors
#   iServiceInformation.sIsScrambled → 1 if currently scrambled (not decrypted)
#                                       0 if NCam/DVB-API has active CW (decrypted)
#
# Author: Ossama Hashim (SamoTech)
# License: MIT

try:
    from enigma import iServiceInformation
except ImportError:
    iServiceInformation = None  # dev/test environment

from Components.config import config


def get_color_for_service(service_ref):
    """
    Returns the foreground hex color string for a service based on CA state.

    Logic:
      - FTA (sIsCrypted == 0)                        → fta_color
      - Encrypted + scrambled (sIsScrambled == 1)    → crypted_color
      - Encrypted + decrypted via NCam (== 0)        → decrypted_color

    Returns:
        str  hex color e.g. '#FFD700', or None if plugin disabled / error
    """
    if config.plugins.channelcolors.enabled.value != "yes":
        return None

    if iServiceInformation is None:
        return None

    try:
        info = service_ref.info()
        if info is None:
            return None

        # Check if channel has CA descriptors at all
        is_crypted = info.getInfo(iServiceInformation.sIsCrypted)

        if is_crypted != 1:
            # Free-to-air
            return config.plugins.channelcolors.fta_color.value

        # Channel is encrypted — check if NCam/DVB-API has decrypted it
        # sIsScrambled: 0 = CW active (NCam decrypting), 1 = still scrambled
        is_scrambled = info.getInfo(iServiceInformation.sIsScrambled)

        if is_scrambled == 0:
            return config.plugins.channelcolors.decrypted_color.value
        else:
            return config.plugins.channelcolors.crypted_color.value

    except Exception as e:
        print("[ChannelColors] get_color_for_service error: %s" % str(e))
        return None


def patch_service_list():
    """
    Monkey-patches Enigma2's ServiceList to apply channel colors
    at render time. Called once at plugin startup from plugin.py.

    This is the standard approach used by plugins that colorize
    the channel list (e.g. OpenWebif, various skin helpers).
    """
    try:
        from Screens.ChannelSelection import ChannelSelectionBase
    except ImportError:
        print("[ChannelColors] Could not import ChannelSelectionBase — skipping patch")
        return

    if getattr(ChannelSelectionBase, '_channel_colors_patched', False):
        return  # already patched, avoid double-patching

    _original_moveToIndex = getattr(ChannelSelectionBase, 'moveToIndex', None)

    original_addService = getattr(ChannelSelectionBase, 'addService', None)

    # Patch the list entry builder to inject foreground color
    try:
        from Components.ServiceList import ServiceList as SL

        _orig_postWidgetCreate = getattr(SL, 'postWidgetCreate', None)

        def _colorized_entry_component(self_sl, service):
            """
            Override: inject foreground color into list entry based on CA state.
            """
            color = get_color_for_service(service)
            entry = self_sl.__class__.__bases__[0].entry_component(self_sl, service) if hasattr(self_sl.__class__.__bases__[0], 'entry_component') else None
            if color and hasattr(self_sl, 'l'):
                # Set per-item foreground color via eListboxPythonMultiContent
                self_sl.l.setForegroundColorSelected(int(color.replace('#', '0x'), 16))
            return entry

        # Use the cleaner skin-level approach: set item foreground via
        # ServiceList's buildEntry / onSelectionChanged path
        _orig_onShow = getattr(ChannelSelectionBase, 'onShow', None) or []

        def _on_selection_changed(self_cs):
            """Called whenever cursor moves — recolor visible entries."""
            try:
                service = self_cs.getCurrentSelection()
                if service:
                    color = get_color_for_service(service)
                    if color and hasattr(self_cs, 'servicelist'):
                        sl = self_cs.servicelist
                        if hasattr(sl, 'l'):
                            rgba = int(color.replace('#', ''), 16) | 0xFF000000
                            sl.l.setForegroundColorSelected(rgba)
            except Exception as e:
                print("[ChannelColors] onSelectionChanged error: %s" % str(e))

        # Append our callback to onSelectionChanged
        if hasattr(ChannelSelectionBase, 'onSelectionChanged'):
            ChannelSelectionBase.onSelectionChanged.append(_on_selection_changed)
        else:
            ChannelSelectionBase.onSelectionChanged = [_on_selection_changed]

        ChannelSelectionBase._channel_colors_patched = True
        print("[ChannelColors] ServiceList patch applied successfully")

    except Exception as e:
        print("[ChannelColors] patch_service_list error: %s" % str(e))
