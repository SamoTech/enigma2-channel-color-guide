# -*- coding: utf-8 -*-
# ColorApplier.py - Channel Colors Plugin
# Author: Ossama Hashim (SamoTech)
# License: MIT
#
# Color logic:
#   White  = FTA          (isCrypted = False)
#   Red    = Encrypted    (isCrypted = True,  CAID NOT in NCam list)
#   Green  = Decrypted    (isCrypted = True,  CAID found in NCam list)
#   Gray   = No signal    (serviceNotAvail)
#
# CAID list is parsed from /etc/ncam/ncam.list at startup and cached.

from Components.config import config
try:
    from Components.MultiContent import parseColor
    from enigma import eServiceCenter
except ImportError:
    parseColor = None


def _log(msg):
    open('/tmp/cc_debug.log', 'a').write('[ChannelColors] ' + msg + '\n')


# ---------------------------------------------------------------------------
# NCam CAID cache
# ---------------------------------------------------------------------------
_ncam_caids = None   # set of int CAIDs, or empty set if file not found

NCAM_LIST_PATHS = [
    '/etc/ncam/ncam.list',
    '/var/etc/ncam/ncam.list',
    '/tmp/ncam.list',
]


def _load_ncam_caids():
    """
    Parse ncam.list and return a set of integer CAIDs.
    ncam.list lines look like:  C: <caid> <provider> ...
    We collect the hex CAID from every 'C:' line.
    """
    caids = set()
    for path in NCAM_LIST_PATHS:
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) >= 2 and parts[0].upper() == 'C:':
                        try:
                            caids.add(int(parts[1], 16))
                        except ValueError:
                            pass
            _log('NCam CAIDs loaded from %s: %d entries' % (path, len(caids)))
            return caids
        except IOError:
            continue
    _log('NCam list not found, decrypted color disabled')
    return set()


def get_ncam_caids():
    global _ncam_caids
    if _ncam_caids is None:
        _ncam_caids = _load_ncam_caids()
    return _ncam_caids


def reload_ncam_caids():
    """Force reload of CAID cache (call after NCam restart)."""
    global _ncam_caids
    _ncam_caids = None
    return get_ncam_caids()


# ---------------------------------------------------------------------------
# Service center helper
# ---------------------------------------------------------------------------
_svc_center = None


def _get_sc():
    global _svc_center
    if _svc_center is None:
        try:
            _svc_center = eServiceCenter.getInstance()
        except Exception:
            pass
    return _svc_center


def _get_service_info(ref):
    """Return (is_encrypted, caid_int) for a service ref."""
    try:
        sc = _get_sc()
        if sc is None:
            return False, 0
        info = sc.info(ref)
        if info is None:
            return False, 0
        encrypted = bool(info.isCrypted())
        # getInfo(iDVBFrontendParameters.flagCrypt) gives the CAID
        try:
            from enigma import iServiceInformation
            caid = info.getInfo(iServiceInformation.sCAIDs)
        except Exception:
            caid = 0
        return encrypted, caid if caid and caid > 0 else 0
    except Exception:
        return False, 0


def _is_ncam_decryptable(ref):
    """
    Return True if the service is encrypted BUT its CAID is in the NCam list.
    We also try reading the CAID directly from the service reference string
    (format: 1:0:1:SID:TID:NID:ONID:0:0:0) — CAID is not there.
    Instead we use isCrypted + getInfoList(sCAIDs).
    """
    try:
        sc = _get_sc()
        if sc is None:
            return False
        info = sc.info(ref)
        if info is None:
            return False
        if not info.isCrypted():
            return False
        ncam = get_ncam_caids()
        if not ncam:
            return False
        try:
            from enigma import iServiceInformation
            caids = info.getInfoList(iServiceInformation.sCAIDs)
            if caids:
                for c in caids:
                    if c in ncam:
                        return True
        except Exception:
            pass
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
def _get_colors():
    try:
        cc = config.plugins.channelcolors
        enc  = parseColor(cc.crypted_color.value)    # Red    - encrypted, no NCam
        dec  = parseColor(cc.decrypted_color.value)  # Green  - decrypted via NCam
        fta  = parseColor(cc.fta_color.value)        # White  - FTA
        return enc, dec, fta
    except Exception:
        return parseColor("#FF3232"), parseColor("#00C800"), parseColor("#FFFFFF")


def _set_base_colors(l, listbox, enc_col, fta_col):
    """
    Base (unmarked) rows = enc_col (Red).
    Marked rows (FTA or NCam-decryptable) use markedForeground.
    We use TWO mark slots:
      - markedForeground         = fta_col  (used for FTA)
      - markedForegroundSelected = dec_col  (overridden per-service in mark loop)
    Gray for no-signal is set via serviceNotAvail.
    """
    try:
        if listbox:
            listbox.setForegroundColor(enc_col)
            listbox.setForegroundColorSelected(enc_col)
        l.colorElements = 0xFFFFFFFF
        l.setColor(l.serviceNotAvail, parseColor("#888888"))
    except Exception as e:
        _log('set_base_colors error: ' + str(e))


# ---------------------------------------------------------------------------
# Main apply
# ---------------------------------------------------------------------------
def _apply_colors(sl):
    try:
        if parseColor is None:
            return
        try:
            if config.plugins.channelcolors.enabled.value != "yes":
                return
        except Exception:
            pass

        l = sl.l
        listbox = getattr(sl, 'instance', None)
        enc_col, dec_col, fta_col = _get_colors()

        # Set base: all rows = Red (encrypted)
        _set_base_colors(l, listbox, enc_col, fta_col)

        try:
            l.initMarked()
            items = l.getList()
            if not items:
                return

            ncam = get_ncam_caids()
            fta_count = enc_count = dec_count = 0

            for ref in items:
                try:
                    sc = _get_sc()
                    if sc is None:
                        continue
                    info = sc.info(ref)
                    if info is None:
                        continue

                    if not info.isCrypted():
                        # FTA - mark with fta_col (White)
                        l.addMarked(ref)
                        fta_count += 1
                    elif ncam:
                        # Check if NCam can decrypt
                        try:
                            from enigma import iServiceInformation
                            caids = info.getInfoList(iServiceInformation.sCAIDs)
                            if caids and any(c in ncam for c in caids):
                                l.addMarked(ref)
                                dec_count += 1
                                continue
                        except Exception:
                            pass
                        enc_count += 1
                    else:
                        enc_count += 1
                except Exception:
                    continue

            _log('FTA=%d DEC=%d ENC=%d' % (fta_count, dec_count, enc_count))

        except Exception as e:
            _log('mark error: ' + str(e))
            return

        # Apply marked color = fta_col for FTA rows
        # NCam rows also get marked but we need a different color.
        # Since eListbox only supports ONE markedForeground color,
        # we use the following trick:
        #   - FTA rows  -> addMarked -> markedForeground = fta_col (White)
        #   - NCam rows -> addMarked -> same slot, but we set it to dec_col (Green)
        # This means FTA and NCam rows share the same mark color.
        # To distinguish them we set markedForeground = dec_col when NCam rows exist,
        # and keep fta_col otherwise. User configures each independently.
        # Best UX: set markedForeground to dec_col (Green) since NCam rows
        # are the interesting ones; FTA gets the same Green (both are "openable").
        try:
            l.setColor(l.markedForeground,        dec_col)
            l.setColor(l.markedForegroundSelected, dec_col)
        except Exception as e:
            _log('setColor error: ' + str(e))

        if listbox:
            listbox.invalidate()

    except Exception as e:
        _log('ERROR: ' + str(e))


def _patch_applySkin(sl):
    orig = sl.applySkin
    l = sl.l
    lb = getattr(sl, 'instance', None)

    def _new(*a, **kw):
        result = orig(*a, **kw)
        try:
            enc_col, dec_col, fta_col = _get_colors()
            _set_base_colors(l, lb, enc_col, fta_col)
            if lb:
                l.setColor(l.markedForeground,        dec_col)
                l.setColor(l.markedForegroundSelected, dec_col)
        except Exception:
            pass
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

    # Pre-load NCam CAIDs at startup
    get_ncam_caids()

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
