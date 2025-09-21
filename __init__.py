# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: output/Live/mac_universal_64_static/Release/python-bundle/MIDI Remote Scripts/Launch_Control_XL/__init__.py
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2024-08-12 14:49:06 UTC (1723474146)

from _Framework.Capabilities import (
    AUTO_LOAD_KEY,
    CONTROLLER_ID_KEY,
    NOTES_CC,
    PORTS_KEY,
    SCRIPT,
    controller_id,
    inport,
    outport,
)
from .LaunchControlXL import LaunchControlXL


def get_capabilities():
    return {
        CONTROLLER_ID_KEY: controller_id(
            vendor_id=4661, product_ids=[97], model_name="Launch Control XL"
        ),
        PORTS_KEY: [
            inport(props=[NOTES_CC, SCRIPT]),
            outport(props=[NOTES_CC, SCRIPT]),
        ],
        AUTO_LOAD_KEY: True,
    }


def create_instance(c_instance):
    return LaunchControlXL(c_instance)
