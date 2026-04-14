# -*- coding: utf-8 -*-
# ColorApplier.py - Channel Colors Plugin v1.7.0
# Author: Ossama Hashim (SamoTech)
# License: MIT
#
# Approach: monkey-patch ServiceList.buildEntry (same as system ColorPatch.py)
# res[1] = parseColor(color) sets per-item foreground color.
#
# Color logic:
#   sIsCrypted == 0              -> fta_color   White  #FFFFFF
#   sIsCrypted == 1 + NCam CAID  -> dec_color   Green  #00C800
#   sIsCrypted == 1 + no NCam    -> enc_color   Red    #FF3232

VERSION = '1.7.0'

import re
import os

LOG = '/tmp/cc_debug.log'


def _log(msg):
    try:
        with open(LOG, 'a') as f:
            f.write('[ChannelColors] ' + str(msg) + '\n')
    except Exception:
        pass


# ---------------------------------------------------------------------------
# lamedb5 CAID table: (sid, tsid, onid) -> set of CAIDs
# ---------------------------------------------------------------------------
_lamedb_caids = None

LAMEDB_PATHS = [
    '/etc/enigma2/lamedb5',
    '/etc/enigma2/lamedb',
]

_SVC_RE   = re.compile(r'^s:([0-9a-fA-F]+):([0-9a-fA-F]+):([0-9a-fA-F]+):([0-9a-fA-F]+):')
_CAPID_RE = re.compile(r',C:([0-9a-fA-F]+)')


def _load_lamedb_caids():
    table = {}
    for path in LAMEDB_PATHS:
        try:
            with open(path, 'r') as f:
                content = f.read()
        except IOError:
            continue
        for line in content.splitlines():
            m = _SVC_RE.match(line)
            if not m:
                continue
            sid  = int(m.group(1), 16)
            tsid = int(m.group(3), 16)
            onid = int(m.group(4), 16)
            caids = set()
            for cm in _CAPID_RE.finditer(line):
                try:
                    caids.add(int(cm.group(1), 16))
                except ValueError:
                    pass
            if caids:
                table[(sid, tsid, onid)] = caids
        if table:
            _log('lamedb [%s]: %d services with CAIDs' % (path, len(table)))
            return table
    _log('lamedb: no CAID data found')
    return table


def get_lamedb_caids():
    global _lamedb_caids
    if _lamedb_caids is None:
        _lamedb_caids = _load_lamedb_caids()
    return _lamedb_caids


def _ref_to_key(ref):
    """Convert eServiceReference to (sid, tsid, onid) tuple."""
    try:
        parts = ref.toString().split(':')
        # format: type:flags:type2:SID:TSID:ONID:...
        if len(parts) < 6:
            return None
        return (int(parts[3], 16), int(parts[4], 16), int(parts[5], 16))
    except Exception:
        return None


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
]

NCAM_HTTP_PORTS = [8181, 8888, 8080]
_CAID_RE  = re.compile(r'([0-9A-Fa-f]{4,5})')
_CAID_MIN = 0x0100
_CAID_MAX = 0x4FFF


def _is_valid_caid(v):
    return _CAID_MIN <= v <= _CAID_MAX


def _fetch_from_file(path):
    caids = set()
    try:
        with open(path, 'r') as f:
            for line in f:
                if 'caid' in line.lower():
                    for m in _CAID_RE.finditer(line):
                        try:
                            v = int(m.group(1), 16)
                            if _is_valid_caid(v):
                                caids.add(v)
                        except ValueError:
                            pass
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
        caids = _fetch_from_file(path)
        if caids:
            _log('ncam.server [%s]: %d CAIDs -> %s' % (
                path, len(caids),
                ','.join(sorted(hex(c) for c in caids))))
            return caids
    for path in SERVICES_PATHS:
        caids = _fetch_from_file(path)
        if caids:
            _log('services [%s]: %d CAIDs' % (path, len(caids)))
            return caids
    try:
        for root, dirs, files in os.walk('/etc/tuxbox/config'):
            for fn in files:
                if fn in ('ncam.server', 'oscam.server'):
                    p = os.path.join(root, fn)
                    caids = _fetch_from_file(p)
                    if caids:
                        _log('auto [%s]: %d CAIDs' % (p, len(caids)))
                        return caids
    except Exception as e:
        _log('walk error: ' + str(e))
    caids = _fetch_caids_webif()
    if caids:
        return caids
    _log('no NCam CAIDs found')
    return set()


def get_ncam_caids():
    global _ncam_caids
    if _ncam_caids is None:
        _ncam_caids = _load_ncam_caids()
    return _ncam_caids


def reload_ncam_caids():
    global _ncam_caids, _lamedb_caids
    _ncam_caids  = None
    _lamedb_caids = None
    n = get_ncam_caids()
    l = get_lamedb_caids()
    _log('reload: NCam=%d lamedb=%d' % (len(n), len(l)))
    return n


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
def _get_colors():
    """
    Returns (enc_color, dec_color, fta_color) as parsed enigma2 color ints.
    enc = Red   #FF3232 - encrypted, NCam cannot decode
    dec = Green #00C800 - encrypted, NCam CAN decode
    fta = White #FFFFFF - free to air
    """
    try:
        from skin import parseColor
        from Components.config import config
        cc = config.plugins.channelcolors
        return (
            parseColor(cc.crypted_color.value),
            parseColor(cc.decrypted_color.value),
            parseColor(cc.fta_color.value),
        )
    except Exception:
        try:
            from skin import parseColor
            return (
                parseColor('#FF3232'),
                parseColor('#00C800'),
                parseColor('#FFFFFF'),
            )
        except Exception:
            return (0xFF3232, 0x00C800, 0xFFFFFF)


# ---------------------------------------------------------------------------
# buildEntry patch  -  per-item color via res[1]
# ---------------------------------------------------------------------------
def patch_service_list():
    open(LOG, 'w').write('[ChannelColors] v%s start\n' % VERSION)

    try:
        from Components.ServiceList import ServiceList
        from enigma import iServiceInformation
    except ImportError as e:
        _log('import error: ' + str(e))
        return

    if getattr(ServiceList, '_cc_patched', False):
        _log('already patched')
        return

    # pre-load caches at startup
    get_ncam_caids()
    get_lamedb_caids()

    _original_buildEntry = ServiceList.buildEntry

    def _patched_buildEntry(self, service, *args, **kwargs):
        res = _original_buildEntry(self, service, *args, **kwargs)
        try:
            from Components.config import config
            if getattr(config.plugins, 'channelcolors', None) and \
               config.plugins.channelcolors.enabled.value != 'yes':
                return res
        except Exception:
            pass

        try:
            if not service:
                return res
            if not (isinstance(res, list) and len(res) > 1):
                return res

            info = service.info()
            if info is None:
                return res

            enc_col, dec_col, fta_col = _get_colors()

            is_crypted = info.getInfo(iServiceInformation.sIsCrypted)

            if is_crypted == 0:
                # Free-to-air
                res[1] = fta_col
            else:
                # Encrypted - check NCam via lamedb
                decoded = False
                ncam   = get_ncam_caids()
                lamedb = get_lamedb_caids()
                if ncam and lamedb:
                    key = _ref_to_key(service)
                    if key:
                        svc_caids = lamedb.get(key, set())
                        if svc_caids and any(c in ncam for c in svc_caids):
                            res[1] = dec_col
                            decoded = True
                if not decoded:
                    res[1] = enc_col

        except Exception as ex:
            _log('buildEntry err: ' + str(ex))

        return res

    ServiceList.buildEntry = _patched_buildEntry
    ServiceList._cc_patched = True
    _log('buildEntry patched OK (v%s)' % VERSION)
    _log('NCam=%d lamedb=%d' % (len(get_ncam_caids()), len(get_lamedb_caids())))
