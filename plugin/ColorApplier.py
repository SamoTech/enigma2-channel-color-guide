# -*- coding: utf-8 -*-
# ColorApplier.py - Channel Colors Plugin
# Author: Ossama Hashim (SamoTech)
# License: MIT
#
# Color logic:
#   FTA     = markedForeground color (default White #FFFFFF)
#   NCam    = markedForeground color (default Green #00C800)
#   Enc     = base foreground color  (default Red   #FF3232)
#   No sig  = serviceNotAvail color  (always  Gray  #888888)
#
# NOTE: eListbox has ONE markedForeground slot.
#   Both FTA and NCam-decryptable channels are "marked".
#   We use dec_col for marked rows. User sets dec_col=White for FTA
#   or dec_col=Green to distinguish NCam channels.
#
# CAID sources (tried in order):
#   1. NCam WebIF JSON API  http://localhost:{port}/api/entitlements
#   2. NCam WebIF HTML      http://localhost:{port}/entitlements.html
#   3. ncam.server file     /etc/ncam/ncam.server  or  /var/etc/ncam/ncam.server

from Components.config import config
try:
    from Components.MultiContent import parseColor
    from enigma import eServiceCenter
except ImportError:
    parseColor = None

import re


def _log(msg):
    open('/tmp/cc_debug.log', 'a').write('[ChannelColors] ' + msg + '\n')


# ---------------------------------------------------------------------------
# NCam CAID cache
# ---------------------------------------------------------------------------
_ncam_caids = None

NCAM_HTTP_PORTS = [8181, 8888, 8080]
NCAM_SERVER_PATHS = [
    '/etc/ncam/ncam.server',
    '/var/etc/ncam/ncam.server',
    '/tmp/ncam.server',
]


def _open_url(url, timeout=3):
    try:
        import urllib2
        resp = urllib2.urlopen(url, timeout=timeout)
        data = resp.read().decode('utf-8', errors='replace')
        resp.close()
        return data
    except ImportError:
        pass
    try:
        import urllib.request
        resp = urllib.request.urlopen(url, timeout=timeout)
        data = resp.read().decode('utf-8', errors='replace')
        resp.close()
        return data
    except Exception:
        return None


def _fetch_caids_json():
    """NCam JSON API: /api/entitlements -> [{"caid":"0500"}, ...]"""
    caids = set()
    for port in NCAM_HTTP_PORTS:
        data = _open_url('http://localhost:%d/api/entitlements' % port, timeout=2)
        if data:
            for m in re.finditer(r'"caid"\s*:\s*"([0-9A-Fa-f]+)"', data):
                try:
                    caids.add(int(m.group(1), 16))
                except ValueError:
                    pass
            if caids:
                _log('NCam JSON API port %d: %d CAIDs' % (port, len(caids)))
                return caids
    return caids


def _fetch_caids_html():
    """Parse NCam entitlements HTML for 4-hex-char CAID table cells."""
    caids = set()
    for port in NCAM_HTTP_PORTS:
        data = _open_url('http://localhost:%d/entitlements.html' % port, timeout=3)
        if data:
            for m in re.finditer(r'<[Tt][Dd][^>]*>\s*([0-9A-Fa-f]{4})\s*</[Tt][Dd]>', data):
                try:
                    val = int(m.group(1), 16)
                    if 0x0100 <= val <= 0x1FFF:
                        caids.add(val)
                except ValueError:
                    pass
            if caids:
                _log('NCam HTML port %d: %d CAIDs' % (port, len(caids)))
                return caids
    return caids


def _fetch_caids_server_file():
    """Parse ncam.server: caid = 0500,0963,..."""
    caids = set()
    for path in NCAM_SERVER_PATHS:
        try:
            with open(path, 'r') as f:
                for line in f:
                    if line.strip().lower().startswith('caid'):
                        for m in re.finditer(r'([0-9A-Fa-f]{4})', line):
                            try:
                                val = int(m.group(1), 16)
                                if 0x0100 <= val <= 0x1FFF:
                                    caids.add(val)
                            except ValueError:
                                pass
            if caids:
                _log('ncam.server %s: %d CAIDs' % (path, len(caids)))
                return caids
        except IOError:
            continue
    return caids


def _load_ncam_caids():
    caids = _fetch_caids_json()
    if caids:
        return caids
    caids = _fetch_caids_html()
    if caids:
        return caids
    caids = _fetch_caids_server_file()
    if caids:
        return caids
    _log('NCam CAIDs: no source found, all encrypted shown as Red')
    return set()


def get_ncam_caids():
    global _ncam_caids
    if _ncam_caids is None:
        _ncam_caids = _load_ncam_caids()
    return _ncam_caids


def reload_ncam_caids():
    global _ncam_caids
    _ncam_caids = None
    result = get_ncam_caids()
    _log('NCam reload: %d CAIDs' % len(result))
    return result


# ---------------------------------------------------------------------------
# Service center
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


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
def _get_colors():
    try:
        cc = config.plugins.channelcolors
        enc = parseColor(cc.crypted_color.value)
        dec = parseColor(cc.decrypted_color.value)
        return enc, dec
    except Exception:
        return parseColor('#FF3232'), parseColor('#00C800')


def _set_base_colors(l, listbox, enc_col):
    try:
        if listbox:
            listbox.setForegroundColor(enc_col)
            listbox.setForegroundColorSelected(enc_col)
        l.colorElements = 0xFFFFFFFF
        l.setColor(l.serviceNotAvail, parseColor('#888888'))
    except Exception as e:
        _log('set_base_colors: ' + str(e))


def _set_marked_color(l, dec_col):
    try:
        l.setColor(l.markedForeground,        dec_col)
        l.setColor(l.markedForegroundSelected, dec_col)
    except Exception as e:
        _log('set_marked_color: ' + str(e))


# ---------------------------------------------------------------------------
# Main apply
# ---------------------------------------------------------------------------
def _apply_colors(sl):
    try:
        if parseColor is None:
            return
        try:
            if config.plugins.channelcolors.enabled.value != 'yes':
                return
        except Exception:
            pass

        l = sl.l
        listbox = getattr(sl, 'instance', None)
        enc_col, dec_col = _get_colors()
        ncam = get_ncam_caids()

        _set_base_colors(l, listbox, enc_col)

        try:
            l.initMarked()
            items = l.getList()
            if not items:
                return

            fta = dec = enc = 0

            for ref in items:
                try:
                    sc = _get_sc()
                    if sc is None:
                        continue
                    info = sc.info(ref)
                    if info is None:
                        continue

                    if not info.isCrypted():
                        l.addMarked(ref)
                        fta += 1
                    elif ncam:
                        try:
                            from enigma import iServiceInformation
                            caids = info.getInfoList(iServiceInformation.sCAIDs)
                            if caids and any(c in ncam for c in caids):
                                l.addMarked(ref)
                                dec += 1
                                continue
                        except Exception:
                            pass
                        enc += 1
                    else:
                        enc += 1
                except Exception:
                    continue

            _log('FTA=%d DEC=%d ENC=%d NCam=%d' % (fta, dec, enc, len(ncam)))

        except Exception as e:
            _log('mark error: ' + str(e))
            return

        _set_marked_color(l, dec_col)

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
            enc_col, dec_col = _get_colors()
            _set_base_colors(l, lb, enc_col)
            _set_marked_color(l, dec_col)
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
