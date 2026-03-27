# -*- coding: utf-8 -*-
from Components.config import config
import os

try:
    from enigma import iServiceInformation, gRGB
except ImportError:
    iServiceInformation = None
    gRGB = None

DEBUG_LOG = "/tmp/cc_debug.log"
_build_call_count = 0


def _log(msg):
    print("[ChannelColors] " + msg)
    try:
        with open(DEBUG_LOG, 'a') as f:
            f.write("[ChannelColors] " + msg + "\n")
    except Exception:
        pass


def _parse_color(hex_str):
    try:
        h = hex_str.strip().lstrip('#')
        return gRGB(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except Exception as e:
        _log("_parse_color error '%s': %s" % (hex_str, str(e)))
        return None


def _get_ca_color(service_ref):
    try:
        if config.plugins.channelcolors.enabled.value != "yes":
            return None
        if iServiceInformation is None or gRGB is None:
            return None
        info = service_ref.info()
        if info is None:
            return None
        is_crypted = info.getInfo(iServiceInformation.sIsCrypted)
        if is_crypted != 1:
            return _parse_color(config.plugins.channelcolors.fta_color.value)
        is_scrambled = info.getInfo(iServiceInformation.sIsScrambled)
        if is_scrambled == 0:
            return _parse_color(config.plugins.channelcolors.decrypted_color.value)
        return _parse_color(config.plugins.channelcolors.crypted_color.value)
    except Exception as e:
        _log("_get_ca_color error: %s" % str(e))
        return None


def patch_service_list():
    global _build_call_count
    try:
        os.remove(DEBUG_LOG)
    except Exception:
        pass

    _log("patch_service_list called")

    try:
        from Components.ServiceList import ServiceList
    except ImportError as e:
        _log("Cannot import ServiceList: %s" % str(e))
        return

    if getattr(ServiceList, '_cc_patched', False):
        _log("Already patched")
        return

    # --- Patch buildEntry to count calls and test color ---
    if hasattr(ServiceList, 'buildEntry'):
        original_buildEntry = ServiceList.buildEntry

        def _patched_buildEntry(self, service):
            global _build_call_count
            original_buildEntry(self, service)
            _build_call_count += 1
            if _build_call_count <= 3:  # log first 3 calls only
                _log("buildEntry called #%d, service type: %s" % (_build_call_count, type(service)))
                try:
                    _log("  l type: %s" % type(self.l))
                    _log("  l methods: %s" % [m for m in dir(self.l) if not m.startswith('__')])
                    color = _get_ca_color(service)
                    _log("  color result: %s" % str(color))
                    if color is not None:
                        self.l.setForegroundColor(color)
                        _log("  setForegroundColor called OK")
                except Exception as e:
                    _log("  hook error: %s" % str(e))

        ServiceList.buildEntry = _patched_buildEntry
        _log("buildEntry patched")

    # --- Also try collectColors ---
    if hasattr(ServiceList, 'collectColors'):
        orig_cc = ServiceList.collectColors
        def _patched_collectColors(self, *args, **kwargs):
            result = orig_cc(self, *args, **kwargs)
            _log("collectColors called, args: %s, result: %s" % (str(args), str(result)))
            return result
        ServiceList.collectColors = _patched_collectColors
        _log("collectColors patched")
    else:
        _log("collectColors not found")

    # --- postWidgetCreate: log self.l methods ---
    if hasattr(ServiceList, 'postWidgetCreate'):
        orig_pwc = ServiceList.postWidgetCreate
        def _debug_pwc(self, instance):
            orig_pwc(self, instance)
            try:
                _log("postWidgetCreate: l type=%s" % type(self.l))
                _log("postWidgetCreate: l methods=%s" % [m for m in dir(self.l) if not m.startswith('__')])
            except Exception as e:
                _log("postWidgetCreate error: %s" % str(e))
        ServiceList.postWidgetCreate = _debug_pwc
        _log("postWidgetCreate hooked")

    ServiceList._cc_patched = True
    _log("patch done - now open channel list to trigger buildEntry")
