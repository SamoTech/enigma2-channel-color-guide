# -*- coding: utf-8 -*-
#
# ColorApplier.py
# Patches the Enigma 2 ServiceList widget at runtime to apply
# channel colors based on encryption / decryption status.
#
# Author: Ossama Hashim (SamoTech)
# License: MIT

try:
    from enigma import eServiceReference, iPlayableService
    from ServiceList import ServiceList          # Enigma 2 internal
except ImportError:
    pass  # Running outside Enigma 2 (dev/test environment)

from Components.config import config


def get_color_for_service(service_ref):
    """
    Returns the appropriate foreground color hex string
    for a given service reference based on its CA status.

    Returns:
        str: hex color code, e.g. '#FFD700'
    """
    if config.plugins.channelcolors.enabled.value != "yes":
        return None

    try:
        info = service_ref.info()
        ca_list = info.getInfoObject(service_ref, iPlayableService.evUpdatedInfo)

        if ca_list:
            # Channel is encrypted — check if currently decrypted via sharing server
            current = service_ref.subType()  # 0 = not decrypted, 1 = decrypted
            if current == 1:
                return config.plugins.channelcolors.decrypted_color.value
            else:
                return config.plugins.channelcolors.crypted_color.value
        else:
            # Free-to-air
            return config.plugins.channelcolors.fta_color.value

    except Exception as e:
        print(f"[ChannelColors] get_color_for_service error: {e}")
        return None
