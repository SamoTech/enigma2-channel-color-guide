# -*- coding: utf-8 -*-
# ColorApplier.py - Channel Colors Plugin
# Author: Ossama Hashim (SamoTech)
# License: MIT
#
# Color logic:
#   FTA (isCrypted=False)          -> fta_color   (default White  #FFFFFF)
#   Encrypted + NCam can decrypt   -> dec_col      (default Green  #00C800)
#   Encrypted + no NCam            -> enc_col base (default Red    #FF3232)
#   No signal                      -> Gray         #888888
#
# NOTE: eListbox has ONE markedForeground slot.
#   We use TWO separate marked passes:
#     Pass 1: mark FTA     -> set markedForeground = fta_color  -> invalidate
#     Pass 2: mark NCam    -> set markedForeground = dec_col    -> invalidate
#   Actually eListbox only has one mark color, so we encode both in one pass
#   using foreground override per-item via setItemForeground if available,
#   otherwise fall back to marking NCam only (FTA stays base=white if user
#   sets enc_col=white, which is wrong).
#
#   REAL FIX: set base foreground = fta_color (White), enc items override Red,
#   NCam items mark Green. But eListbox only allows ONE foreground override.
#
#   FINAL APPROACH (matches original plugin intent):
#     - Base foreground = Red  (all channels start Red)
#     - Mark FTA channels      -> markedForeground = White
#     - After FTA mark+invalidate, re-mark NCam channels -> markedForeground = Green
#   This requires two invalidate passes which flickers.
#
#   SIMPLEST CORRECT APPROACH:
#     - Use colorElements to set per-serviceType color if supported
#     - OR: Accept that marked = Green, and set base = Red
#       FTA = White via a SECOND separate marked list is not possible
#
#   ENIGMA2 REALITY: ServiceList has l.setColor(l.serviceNotAvail, gray)
#   and l.setColor(l.markedForeground, color) for marked items.
#   FTA and NCam-decryptable both get marked -> same Green color.
#   To show FTA as White: set base=White, mark encrypted=Red (inverted logic).
#
#   INVERTED LOGIC (correct for 3 colors):
#     - Base foreground = White  (FTA default - most channels are FTA or NCam)
#     - Mark ENCRYPTED (no NCam) -> markedForeground = Red
#     - For NCam channels: they are NOT marked -> stay White? No, need Green.
#
#   ONLY WAY for 3 distinct colors in enigma2 ServiceList:
#     Use colorElements bitmask with renderer that supports it, OR
#     patch the renderer itself.
#
#   PRACTICAL SOLUTION (2 colors only, as original plugin worked):
#     - Base = Red    (encrypted)
#     - Marked = Green (FTA + NCam decryptable)
#     - User sets Green=#FFFFFF for FTA feel, or accepts Green for both
#
# CAID source: lamedb5  C:cached_capid fields

VERSION = '1.6.0'

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
# lamedb5 CAID table:  (sid, tsid, onid) -> set of CAIDs
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
    _log('lamedb: no CAID data')
    return table


def get_lamedb_caids():
    global _lamedb_caids
    if _lamedb_caids is None:
        _lamedb_caids = _load_lamedb_caids()
    return _lamedb_caids


def _ref_to_key(ref):
    try:
        parts = ref.toString().split(':')
        if len(parts) < 6:
            return None
        return (int(parts[3], 16), int(parts[4], 16), int(parts[5], 16))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# NCam CAID cache  (from ncam.server)
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
_CAID_RE  = re.compile(r'([0-9A-Fa-f]{4,5})')
_CAID_MIN = 0x0100
_CAID_MAX = 0x4FFF


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


def _fetch_from_file(path):
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
        caids = _fetch_from_file(path)
        if caids:
            _log('ncam.server [%s]: %d CAIDs -> %s' % (
                path, len(caids), ','.join(sorted(hex(c) for c in caids))))
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
    _ncam_caids = None
    _lamedb_caids = None
    n = get_ncam_caids()
    l = get_lamedb_caids()
    _log('reload: NCam=%d lamedb=%d' % (len(n), len(l)))
    return n


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
    """
    Returns (enc_col, dec_col, fta_col)
    enc = Red   - encrypted, NCam cannot decode
    dec = Green - encrypted, NCam CAN decode
    fta = White - free to air
    """
    try:
        cc = config.plugins.channelcolors
        enc = parseColor(cc.crypted_color.value)
        dec = parseColor(cc.decrypted_color.value)
        fta = parseColor(cc.fta_color.value)
        return enc, dec, fta
    except Exception:
        return parseColor('#FF3232'), parseColor('#00C800'), parseColor('#FFFFFF')


# ---------------------------------------------------------------------------
# Main apply  -  3-color approach:
#
#  enigma2 ServiceList supports:
#    - ONE base foreground color  (setForegroundColor)
#    - ONE marked foreground color (setColor markedForeground)
#    - serviceNotAvail color
#
#  To get 3 colors we do TWO passes with invalidate between them:
#    Pass A: base=White(FTA), mark Encrypted(Red), invalidate
#    Pass B: base=White(FTA), mark NCam-dec(Green), invalidate
#  But this causes flicker and is not reliable.
#
#  BEST SINGLE-PASS APPROACH:
#    base = Red   (encrypted - majority of paid channels)
#    mark = Green (FTA + NCam) using markedForeground
#    FTA vs NCam distinction: NOT possible with standard ServiceList
#    unless we use a custom renderer.
#
#  USER CONFIG: if user wants FTA=White, set dec_col=White
#               if user wants NCam=Green, set dec_col=Green
#               Both FTA and NCam share the same marked color.
#
#  This matches the ORIGINAL plugin behavior described in the README:
#    Green = FTA  (free to air)  <- user sets dec_col=Green, enc_col=Red
#    Red   = Encrypted
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

        l       = sl.l
        listbox = getattr(sl, 'instance', None)
        enc_col, dec_col, fta_col = _get_colors()
        ncam   = get_ncam_caids()
        lamedb = get_lamedb_caids()

        # Base = Red (encrypted channels)
        try:
            if listbox:
                listbox.setForegroundColor(enc_col)
                listbox.setForegroundColorSelected(enc_col)
            l.colorElements = 0xFFFFFFFF
            l.setColor(l.serviceNotAvail, parseColor('#888888'))
        except Exception as e:
            _log('base_colors: ' + str(e))

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

                    crypted = info.isCrypted()

                    if not crypted:
                        # FTA -> mark (will show markedForeground color)
                        l.addMarked(ref)
                        fta += 1
                    else:
                        # Encrypted -> check if NCam can decode via lamedb
                        decoded = False
                        if ncam and lamedb:
                            key = _ref_to_key(ref)
                            if key:
                                svc_caids = lamedb.get(key, set())
                                if svc_caids and any(c in ncam for c in svc_caids):
                                    l.addMarked(ref)
                                    dec += 1
                                    decoded = True
                        if not decoded:
                            enc += 1

                except Exception as ex:
                    _log('ref err: ' + str(ex))
                    continue

            _log('FTA=%d DEC=%d ENC=%d NCam=%d lamedb=%d' % (
                fta, dec, enc, len(ncam), len(lamedb)))

        except Exception as e:
            _log('mark: ' + str(e))
            return

        # marked color = Green (NCam) for enc channels
        # For FTA: ideally White, but both FTA+NCam share one marked color
        # Set to dec_col (Green by default) - user can change in settings
        try:
            l.setColor(l.markedForeground,         dec_col)
            l.setColor(l.markedForegroundSelected,  dec_col)
        except Exception as e:
            _log('marked_color: ' + str(e))

        if listbox:
            listbox.invalidate()

    except Exception as e:
        _log('ERROR: ' + str(e))


def _patch_applySkin(sl):
    orig = sl.applySkin
    l    = sl.l
    lb   = getattr(sl, 'instance', None)

    def _new(*a, **kw):
        result = orig(*a, **kw)
        try:
            enc_col, dec_col, _ = _get_colors()
            if lb:
                lb.setForegroundColor(enc_col)
                lb.setForegroundColorSelected(enc_col)
            l.colorElements = 0xFFFFFFFF
            l.setColor(l.serviceNotAvail, parseColor('#888888'))
            l.setColor(l.markedForeground,        dec_col)
            l.setColor(l.markedForegroundSelected, dec_col)
        except Exception:
            pass
        return result

    sl.applySkin = _new


def patch_service_list():
    open(LOG, 'w').write('[ChannelColors] v%s start\n' % VERSION)
    try:
        from Screens.ChannelSelection import ChannelSelectionBase
    except ImportError as e:
        _log('import: ' + str(e))
        return

    if getattr(ChannelSelectionBase, '_cc_patched', False):
        return

    get_ncam_caids()
    get_lamedb_caids()

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
