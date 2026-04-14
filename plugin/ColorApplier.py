# -*- coding: utf-8 -*-
# ColorApplier.py - Channel Colors Plugin
# Author: Ossama Hashim (SamoTech)
# License: MIT
#
# Color logic:
#   FTA / NCam-decryptable  = markedForeground color (Green #00C800)
#   Encrypted (no NCam)     = base foreground color  (Red   #FF3232)
#   No signal               = serviceNotAvail color  (Gray  #888888)
#
# NCam 15.7 r1 has NO JSON API — WebIF returns HTML only.
# CAID sources tried in order:
#   1. /etc/tuxbox/config/ncam.server       (caid = 0500,0604,...)
#   2. /etc/tuxbox/config/ncam.services     ([service] caid = 1833,...)
#   3. /etc/tuxbox/config/oscam.services
#   4. Auto-walk /etc/tuxbox/config/ for any ncam.server
#   5. NCam WebIF HTML scrape  localhost:8181/entitlements.html
#
# CAID regex: ([0-9A-Fa-f]{4,5})  range: 0x0100 - 0x4FFF
# Covers: 0500 0604 090F 0E00 1010 1801 2600 2602 2610 4AE1

from Components.config import config
try:
    from Components.MultiContent import parseColor
    from enigma import eServiceCenter
except ImportError:
    parseColor = None

import re
import os

LOG = '/tmp/cc_debug.log'


def _log(msg):
    try:
        open(LOG, 'a').write('[ChannelColors] ' + str(msg) + '\n')
    except Exception:
        pass


# ---------------------------------------------------------------------------
# NCam CAID cache
# ---------------------------------------------------------------------------
_ncam_caids = None

NCAM_SERVER_PATHS = [
    '/etc/tuxbox/config/ncam.server',
    '/etc/tuxbox/config/RevCam-emu/ncam.server',
    '/etc/tuxbox/config/emu+suptv/ncam.server',
    '/etc/tuxbox/config/supcam-emu/ncam.server',
    '/etc/tuxbox/config/emu+RevcamV2/ncam.server',
    '/etc/ncam/ncam.server',
    '/var/etc/ncam/ncam.server',
]

SERVICES_PATHS = [
    '/etc/tuxbox/config/ncam.services',
    '/etc/tuxbox/config/oscam.services',
    '/etc/tuxbox/config/RevCam-emu/ncam.services',
    '/etc/tuxbox/config/oscam-emu/oscam.services',
]

NCAM_HTTP_PORTS = [8181, 8888, 8080]

# Match 4 or 5 hex chars (covers 0500..4AE1..FFFFF range split by comma)
_CAID_RE = re.compile(r'([0-9A-Fa-f]{4,5})')
_CAID_MIN = 0x0100
_CAID_MAX = 0x4FFF  # extended: covers 2600,2602,2610,4AE1


def _is_valid_caid(v):
    return _CAID_MIN <= v <= _CAID_MAX


def _parse_caid_line(line):
    caids = set()
    for m in _CAID_RE.finditer(line):
        try:
            v = int(m.group(1), 16)
            if _is_valid_caid(v):
                caids.add(v)
        except ValueError:
            pass
    return caids


def _fetch_from_server_file(path):
    caids = set()
    try:
        with open(path, 'r') as f:
            for line in f:
                if 'caid' in line.lower():
                    caids |= _parse_caid_line(line)
    except IOError:
        return set()
    return caids


def _fetch_from_services_file(path):
    caids = set()
    try:
        with open(path, 'r') as f:
            for line in f:
                if 'caid' in line.lower():
                    caids |= _parse_caid_line(line)
    except IOError:
        return set()
    return caids


def _open_url(url, timeout=4):
    try:
        import urllib2
        r = urllib2.urlopen(url, timeout=timeout)
        d = r.read().decode('utf-8', errors='replace')
        r.close()
        return d
    except ImportError:
        pass
    try:
        import urllib.request
        r = urllib.request.urlopen(url, timeout=timeout)
        d = r.read().decode('utf-8', errors='replace')
        r.close()
        return d
    except Exception:
        pass
    return None


def _fetch_caids_webif():
    caids = set()
    td_re = re.compile(r'<[Tt][Dd][^>]*>\s*([0-9A-Fa-f]{4,5})\s*</[Tt][Dd]>')
    for port in NCAM_HTTP_PORTS:
        data = _open_url('http://localhost:%d/entitlements.html' % port)
        if not data:
            continue
        for m in td_re.finditer(data):
            try:
                v = int(m.group(1), 16)
                if _is_valid_caid(v):
                    caids.add(v)
            except ValueError:
                pass
        if caids:
            _log('WebIF port %d: %d CAIDs' % (port, len(caids)))
            return caids
    return caids


def _load_ncam_caids():
    for path in NCAM_SERVER_PATHS:
        caids = _fetch_from_server_file(path)
        if caids:
            _log('ncam.server [%s]: %d CAIDs -> %s' % (
                path, len(caids),
                ','.join(sorted(hex(c) for c in caids))))
            return caids

    for path in SERVICES_PATHS:
        caids = _fetch_from_services_file(path)
        if caids:
            _log('services [%s]: %d CAIDs' % (path, len(caids)))
            return caids

    try:
        base = '/etc/tuxbox/config'
        for root, dirs, files in os.walk(base):
            for fn in files:
                if fn in ('ncam.server', 'oscam.server'):
                    p = os.path.join(root, fn)
                    caids = _fetch_from_server_file(p)
                    if caids:
                        _log('auto [%s]: %d CAIDs' % (p, len(caids)))
                        return caids
    except Exception as e:
        _log('walk: ' + str(e))

    caids = _fetch_caids_webif()
    if caids:
        return caids

    _log('no CAIDs found')
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
    _log('reload: %d CAIDs' % len(result))
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
        _log('base_colors: ' + str(e))


def _set_marked_color(l, dec_col):
    try:
        l.setColor(l.markedForeground,         dec_col)
        l.setColor(l.markedForegroundSelected,  dec_col)
    except Exception as e:
        _log('marked_color: ' + str(e))


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
                    else:
                        marked = False
                        if ncam:
                            try:
                                from enigma import iServiceInformation
                                caids = info.getInfoList(iServiceInformation.sCAIDs)
                                if caids and any(c in ncam for c in caids):
                                    l.addMarked(ref)
                                    dec += 1
                                    marked = True
                            except Exception:
                                pass
                        if not marked:
                            enc += 1
                except Exception:
                    continue

            _log('FTA=%d DEC=%d ENC=%d NCam=%d' % (fta, dec, enc, len(ncam)))

        except Exception as e:
            _log('mark: ' + str(e))
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
    open(LOG, 'w').write('[ChannelColors] start\n')
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
