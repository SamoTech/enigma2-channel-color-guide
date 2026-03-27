# -*- coding: utf-8 -*-
#
# ColorApplier.py - Debug version to find correct hook point
# Author: Ossama Hashim (SamoTech)

from Components.config import config

try:
    from enigma import iServiceInformation, gRGB, eServiceReference
except ImportError:
    iServiceInformation = None
    gRGB = None


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
        print("[ChannelColors] _get_ca_color error: %s" % str(e))
        return None


def patch_service_list():
    try:
        from Components.ServiceList import ServiceList
    except ImportError:
        print("[ChannelColors] Cannot import ServiceList")
        return

    # DEBUG: log all methods/attributes of ServiceList
    print("[ChannelColors] ServiceList methods: %s" % [m for m in dir(ServiceList) if not m.startswith('__')])

    if getattr(ServiceList, '_cc_patched', False):
        print("[ChannelColors] Already patched")
        return

    # DEBUG: check if buildEntry exists
    if hasattr(ServiceList, 'buildEntry'):
        print("[ChannelColors] buildEntry EXISTS - patching")
        original_buildEntry = ServiceList.buildEntry

        def _patched_buildEntry(self, service):
            original_buildEntry(self, service)
            try:
                color = _get_ca_color(service)
                if color is not None:
                    self.l.setForegroundColor(color)
            except Exception as e:
                print("[ChannelColors] buildEntry error: %s" % str(e))

        ServiceList.buildEntry = _patched_buildEntry
        print("[ChannelColors] buildEntry patched OK")
    else:
        print("[ChannelColors] buildEntry NOT FOUND - trying GUITemplate / invalidate approach")
        # Fallback: patch postWidgetCreate to hook invalidate
        try:
            orig_postWidgetCreate = ServiceList.postWidgetCreate

            def _patched_postWidgetCreate(self, instance):
                orig_postWidgetCreate(self, instance)
                print("[ChannelColors] postWidgetCreate called, l type: %s" % type(self.l))
                print("[ChannelColors] l methods: %s" % [m for m in dir(self.l) if not m.startswith('__')])
            ServiceList.postWidgetCreate = _patched_postWidgetCreate
            print("[ChannelColors] postWidgetCreate patched for debug")
        except Exception as e:
            print("[ChannelColors] postWidgetCreate patch error: %s" % str(e))

    ServiceList._cc_patched = True
    print("[ChannelColors] patch_service_list done")
