# -*- coding: utf-8 -*-
#
# ColorApplier.py
# OpenATV 7.x uses a C++ template-based ServiceList renderer.
# buildEntry() exists in Python but is never called - the C++ side handles it.
#
# Correct approach for OpenATV 7.x:
#   Override ServiceList.addService to inject foreground color per row
#   via eListboxPythonMultiContent color index on the list content object.
#
# Author: Ossama Hashim (SamoTech)
# License: MIT

from Components.config import config
import os

try:
    from enigma import iServiceInformation, gRGB, eListboxPythonMultiContent
except ImportError:
    iServiceInformation = None
    gRGB = None
    eListboxPythonMultiContent = None

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

    # postWidgetCreate: runs after the C++ widget is created
    # This is where self.l (the listbox content object) becomes available
    # We use it to hook invalidate so colors refresh when list reloads
    if hasattr(ServiceList, 'postWidgetCreate'):
        orig_pwc = ServiceList.postWidgetCreate

        def _patched_pwc(self, instance):
            orig_pwc(self, instance)
            try:
                _log("postWidgetCreate: l type=%s" % type(self.l))
                _log("postWidgetCreate: l methods=%s" % [m for m in dir(self.l) if not m.startswith('__')])
            except Exception as e:
                _log("postWidgetCreate error: %s" % str(e))

        ServiceList.postWidgetCreate = _patched_pwc
        _log("postWidgetCreate hooked")

    # finishFill: called after the list is fully populated
    # This is our best hook point - iterate all items and set colors
    if hasattr(ServiceList, 'finishFill'):
        orig_ff = ServiceList.finishFill

        def _patched_finishFill(self, *args, **kwargs):
            orig_ff(self, *args, **kwargs)
            _log("finishFill called - applying colors")
            _apply_colors_to_list(self)

        ServiceList.finishFill = _patched_finishFill
        _log("finishFill patched")
    else:
        _log("finishFill not found")

    # fillFinished: alternative name used in some builds
    if hasattr(ServiceList, 'fillFinished'):
        orig_ffd = ServiceList.fillFinished

        def _patched_fillFinished(self, *args, **kwargs):
            result = orig_ffd(self, *args, **kwargs)
            _log("fillFinished called - applying colors")
            _apply_colors_to_list(self)
            return result

        ServiceList.fillFinished = _patched_fillFinished
        _log("fillFinished patched")
    else:
        _log("fillFinished not found")

    ServiceList._cc_patched = True
    _log("patch done")


def _apply_colors_to_list(service_list):
    """
    Iterate over the populated list and apply foreground colors.
    Works with the eListboxServiceContent C++ object via getList().
    """
    try:
        _log("_apply_colors_to_list: type(service_list)=%s" % type(service_list))
        # Try getList() - returns the underlying list content
        if hasattr(service_list, 'getList'):
            items = service_list.getList()
            _log("getList() returned type=%s len=%s" % (type(items), str(len(items)) if items else 'None'))
        # Try accessing list directly
        if hasattr(service_list, 'list'):
            _log("service_list.list type=%s" % type(service_list.list))
        # Try l object methods
        if hasattr(service_list, 'l'):
            l = service_list.l
            _log("l type=%s" % type(l))
            _log("l methods=%s" % [m for m in dir(l) if not m.startswith('__')])
    except Exception as e:
        _log("_apply_colors_to_list error: %s" % str(e))
