# -*- coding: utf-8 -*-
# ColorApplier.py - Channel Colors Plugin
# Author: Ossama Hashim (SamoTech)
# License: MIT
#
# How it works:
# - Hooks into ChannelSelectionBase.__init__
# - Uses eServiceCenter.info().isCrypted() to detect FTA vs encrypted
# - Sets eListbox base foreground = encrypted color
# - Marks FTA services with addMarked() -> markedForeground = FTA color
# - Patches applySkin() to survive setRoot() skin re-applies
# - Calls eListbox.setForegroundColor() directly (bypasses skin hardcoded white)
# - Saves/restores cursor position around setRoot() to avoid jumping to first item

from Components.config import config
try:
    from Components.MultiContent import parseColor
    from enigma import eServiceCenter
except ImportError:
    parseColor = None


def _log(msg):
    open('/tmp/cc_debug.log', 'a').write('[ChannelColors] ' + msg + '\n')


_svc_center = None


def _get_sc():
    global _svc_center
    if _svc_center is None:
        try:
            _svc_center = eServiceCenter.getInstance()
        except Exception:
            pass
    return _svc_center


def _is_encrypted(ref):
    try:
        sc = _get_sc()
        if sc is None:
            return False
        info = sc.info(ref)
        return info is not None and info.isCrypted()
    except Exception:
        return False


def _get_colors():
    try:
        cc = config.plugins.channelcolors
        fta = parseColor(cc.fta_color.value)
        enc = parseColor(cc.crypted_color.value)
        return fta, enc
    except Exception:
        return parseColor("#00C800"), parseColor("#FF3232")


def _set_colors(l, listbox, enc_col, fta_col):
    """
    Base color (eListbox foreground) = encrypted color for all rows.
    Marked items (FTA) use markedForeground = fta_col.
    serviceNotAvail = gray for no-signal channels.
    """
    try:
        if listbox:
            listbox.setForegroundColor(enc_col)
            listbox.setForegroundColorSelected(enc_col)
        l.colorElements = 0xFFFFFFFF
        l.setColor(l.markedForeground,         fta_col)
        l.setColor(l.markedForegroundSelected,  fta_col)
        l.setColor(l.serviceNotAvail,           parseColor("#888888"))
    except Exception as e:
        _log('set_colors error: ' + str(e))


def _apply_colors(sl):
    try:
        if parseColor is None:
            return

        # Respect enabled toggle
        try:
            if config.plugins.channelcolors.enabled.value != "yes":
                return
        except Exception:
            pass

        l = sl.l
        listbox = getattr(sl, 'instance', None)
        fta_col, enc_col = _get_colors()

        # Save current selected service BEFORE setRoot resets position
        current = sl.getCurrent()

        # setRoot reloads the service list (resets cursor to top)
        root = sl.getRoot()
        if root:
            sl.setRoot(root)

        # Apply colors after setRoot
        _set_colors(l, listbox, enc_col, fta_col)

        # Mark all FTA services -> they get markedForeground (fta_col)
        try:
            l.initMarked()
            for ref in l.getList():
                if not _is_encrypted(ref):
                    l.addMarked(ref)
        except Exception as e:
            _log('mark error: ' + str(e))

        # Re-apply colors after marking
        _set_colors(l, listbox, enc_col, fta_col)

        # Restore cursor to previously selected channel
        if current and current.valid():
            try:
                sl.moveToService(current)
            except Exception as e:
                _log('restore cursor error: ' + str(e))

        if listbox:
            listbox.invalidate()

    except Exception as e:
        _log('ERROR: ' + str(e))


def _patch_applySkin(sl):
    """
    Wrap applySkin so our colors survive every skin re-apply
    triggered by setRoot() or screen transitions.
    """
    orig = sl.applySkin
    l = sl.l
    lb = getattr(sl, 'instance', None)

    def _new(*a, **kw):
        result = orig(*a, **kw)
        fta_col, enc_col = _get_colors()
        _set_colors(l, lb, enc_col, fta_col)
        return result

    sl.applySkin = _new


def patch_service_list():
    open('/tmp/cc_debug.log', 'w').write('[ChannelColors] start\n')
    try:
        from Screens.ChannelSelection import ChannelSelectionBase
    except ImportError as e:
        _log('import: ' + str(e))
        return

    if getattr(ChannelSelectionBase, '_cc_patched', False):
        return

    orig_init = ChannelSelectionBase.__init__

    def _new_init(self, *a, **kw):
        orig_init(self, *a, **kw)
        try:
            _patch_applySkin(self.servicelist)
            _apply_colors(self.servicelist)
            self.onShow.append(lambda: _apply_colors(self.servicelist))
        except Exception as e:
            _log('hook: ' + str(e))

    ChannelSelectionBase.__init__ = _new_init
    ChannelSelectionBase._cc_patched = True
    _log('patched OK')
