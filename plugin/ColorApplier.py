# -*- coding: utf-8 -*-
# ColorApplier.py - Channel Colors Plugin v1.8.0
# Author: Ossama Hashim (SamoTech)
# License: MIT
#
# KEY FIX v1.8.0:
#   sIsCrypted is UNRELIABLE in buildEntry (no live tuner = always 0)
#   Instead: use lamedb5 C: fields directly
#     - service has C: CAIDs in lamedb  -> encrypted
#     - service has NO C: CAIDs         -> FTA
#     - encrypted + NCam CAID match     -> Green
#     - encrypted + no NCam match       -> Red
#     - FTA (no C: fields)              -> White

VERSION = '1.8.0'

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
# lamedb5 CAID table
# key: (sid, tsid, onid) -> set of CAIDs  (empty set = FTA)
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
        count_enc = 0
        count_fta = 0
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
            table[(sid, tsid, onid)] = caids
            if caids:
                count_enc += 1
            else:
                count_fta += 1
        if table:
            _log('lamedb [%s]: %d total (%d enc, %d fta)' % (
                path, len(table), count_enc, count_fta))
            return table
    _log('lamedb: not found')
    return table


def get_lamedb_caids():
    global _lamedb_caids
    if _lamedb_caids is None:
        _lamedb_caids = _load_lamedb_caids()
    return _lamedb_caids


def _ref_to_key(ref):
    """eServiceReference -> (sid, tsid, onid)"""
    try:
        parts = ref.toString().split(':')
        # format: 1:0:1:SID:TSID:ONID:NAMESPACE:...
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
        _log('walk: ' + str(e))
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
    _ncam_caids   = None
    _lamedb_caids = None
    n = get_ncam_caids()
    l = get_lamedb_caids()
    _log('reload: NCam=%d lamedb=%d' % (len(n), len(l)))
    return n


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
def _get_colors():
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
# buildEntry patch
#
# Logic (pure lamedb, no sIsCrypted):
#   key not in lamedb OR lamedb[key] empty  -> FTA   -> White
#   lamedb[key] has CAIDs + NCam match      -> DEC   -> Green
#   lamedb[key] has CAIDs + no NCam match   -> ENC   -> Red
# ---------------------------------------------------------------------------
def patch_service_list():
    open(LOG, 'w').write('[ChannelColors] v%s start\n' % VERSION)

    try:
        from Components.ServiceList import ServiceList
    except ImportError as e:
        _log('import error: ' + str(e))
        return

    if getattr(ServiceList, '_cc_patched', False):
        _log('already patched')
        return

    get_ncam_caids()
    get_lamedb_caids()

    _orig = ServiceList.buildEntry

    def _patched(self, service, *args, **kwargs):
        res = _orig(self, service, *args, **kwargs)
        try:
            try:
                from Components.config import config
                if config.plugins.channelcolors.enabled.value != 'yes':
                    return res
            except Exception:
                pass

            if not service:
                return res
            if not (isinstance(res, list) and len(res) > 1):
                return res

            enc_col, dec_col, fta_col = _get_colors()
            ncam   = get_ncam_caids()
            lamedb = get_lamedb_caids()

            key       = _ref_to_key(service)
            svc_caids = lamedb.get(key, None) if key else None

            if not svc_caids:          # None (not in lamedb) or empty set (FTA)
                res[1] = fta_col
            elif ncam and any(c in ncam for c in svc_caids):
                res[1] = dec_col       # Green - NCam can decode
            else:
                res[1] = enc_col       # Red - encrypted, no NCam

        except Exception as ex:
            _log('buildEntry err: ' + str(ex))

        return res

    ServiceList.buildEntry = _patched
    ServiceList._cc_patched = True
    _log('patched OK v%s | NCam=%d lamedb=%d' % (
        VERSION, len(get_ncam_caids()), len(get_lamedb_caids())))
