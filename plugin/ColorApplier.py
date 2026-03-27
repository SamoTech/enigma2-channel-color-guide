# -*- coding: utf-8 -*-
# ColorApplier.py - OpenATV 7.x
# eListboxServiceContent color slots are PROPERTIES not methods - assign directly
# Author: Ossama Hashim (SamoTech)
from Components.config import config
try:
    from enigma import iServiceInformation, gRGB
except ImportError:
    iServiceInformation = None
    gRGB = None

def _log(msg):
    open('/tmp/cc_debug.log', 'a').write('[ChannelColors] ' + msg + '\n')

def _parse_color(hex_str):
    try:
        h = hex_str.strip().lstrip('#')
        return gRGB(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except Exception as e:
        _log('_parse_color error: ' + str(e))
        return None

def _apply_colors(sl):
    try:
        if config.plugins.channelcolors.enabled.value != 'yes':
            return
        if gRGB is None:
            return
        l = sl.l
        fta_color     = _parse_color(config.plugins.channelcolors.fta_color.value)
        crypted_color = _parse_color(config.plugins.channelcolors.crypted_color.value)
        decrypt_color = _parse_color(config.plugins.channelcolors.decrypted_color.value)

        # These are PROPERTIES (int slots), assign with = not ()
        if fta_color:
            l.setColor(0, fta_color)          # normal foreground = FTA
        if crypted_color:
            l.serviceNotAvail = crypted_color  # scrambled rows = encrypted
        if decrypt_color:
            l.servicePseudoRecorded = decrypt_color  # pseudo = NCam decrypted

        # setCryptoIconMode IS a method
        if hasattr(l, 'setCryptoIconMode'):
            l.setCryptoIconMode(2)

        root = sl.getRoot()
        if root:
            sl.setRoot(root)
        _log('_apply_colors OK')
    except Exception as e:
        _log('_apply_colors error: ' + str(e))

def patch_service_list():
    open('/tmp/cc_debug.log', 'w').write('[ChannelColors] patch_service_list called\n')
    try:
        from Screens.ChannelSelection import ChannelSelectionBase
    except ImportError as e:
        _log('import error: ' + str(e))
        return
    if getattr(ChannelSelectionBase, '_cc_patched', False):
        return
    orig_init = ChannelSelectionBase.__init__
    def _patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        try:
            _apply_colors(self.servicelist)
            if hasattr(self, 'onShow'):
                self.onShow.append(lambda: _apply_colors(self.servicelist))
            _log('init hook OK')
        except Exception as e:
            _log('init hook error: ' + str(e))
    ChannelSelectionBase.__init__ = _patched_init
    ChannelSelectionBase._cc_patched = True
    _log('patched OK')
