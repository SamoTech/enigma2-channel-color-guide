# -*- coding: utf-8 -*-
from Components.config import config
import os

try:
    from enigma import iServiceInformation, gRGB
except ImportError:
    iServiceInformation = None
    gRGB = None

DEBUG_LOG = "/tmp/cc_debug.log"


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
    except Exception:
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
    # Clear previous debug log
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

    _log("ServiceList imported OK")

    # Log all public methods
    methods = [m for m in dir(ServiceList) if not m.startswith('__')]
    _log("ServiceList attrs: " + str(methods))

    if getattr(ServiceList, '_cc_patched', False):
        _log("Already patched - skip")
        return

    if hasattr(ServiceList, 'buildEntry'):
        _log("buildEntry found - patching")
        original_buildEntry = ServiceList.buildEntry

        def _patched_buildEntry(self, service):
            original_buildEntry(self, service)
            try:
                color = _get_ca_color(service)
                if color is not None:
                    self.l.setForegroundColor(color)
                    _log("setForegroundColor called for service")
            except Exception as e:
                _log("buildEntry hook error: %s" % str(e))

        ServiceList.buildEntry = _patched_buildEntry
        _log("buildEntry patched OK")
    else:
        _log("buildEntry NOT FOUND")

    # Also log l methods via postWidgetCreate
    if hasattr(ServiceList, 'postWidgetCreate'):
        orig_pwc = ServiceList.postWidgetCreate
        def _debug_pwc(self, instance):
            orig_pwc(self, instance)
            try:
                _log("l type: " + str(type(self.l)))
                _log("l methods: " + str([m for m in dir(self.l) if not m.startswith('__')]))
            except Exception as e:
                _log("postWidgetCreate debug error: %s" % str(e))
        ServiceList.postWidgetCreate = _debug_pwc
        _log("postWidgetCreate debug hook added")

    ServiceList._cc_patched = True
    _log("patch_service_list done")
