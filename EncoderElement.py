# uncompyle6 version 3.9.1
# Python bytecode version base 3.7.0 (3394)
# Decompiled from: Python 3.12.2 (main, Feb  6 2024, 20:19:44) [Clang 15.0.0 (clang-1500.1.0.2.5)]
# Embedded file name: output/Live/mac_universal_64_static/Release/python-bundle/MIDI Remote Scripts/_Framework/EncoderElement.py
# Compiled at: 2024-03-09 01:30:22
# Size of source mod 2**32: 7712 bytes
from _Framework.EncoderElement import EncoderElement as EncoderElementBase
import logging


def value2color(value, min_val, max_val):
    assert min_val <= value <= max_val, "Something is horribly wrong"
    norm_val = (100/(max_val - min_val))*value - min_val*(100/(max_val - min_val))

    color = [0, 16, 96, 61, 58, 19, 31]
    color_code = int(norm_val/(int(100/(len(color)))))
    picked = 3
    if color_code < len(color):
        picked = color[int(norm_val/(int(100/(len(color)))))]
    return picked

class EncoderElement(EncoderElementBase):
    def __init__(self, msg_type, channel, identifier, map_mode, encoder_sensitivity = None, but_light = None, *a, **k):
        self.but_light = but_light
        super(EncoderElement, self).__init__(msg_type, channel, identifier, map_mode, encoder_sensitivity, *a, **k)
        self.add_value_listener(self._on_encoder_moved)
    def receive_value(self, value):
        self._set_lightval()

    def _on_encoder_moved(self, value):
        # Keeping this here to not forget how listeners work
        pass

    def _set_lightval(self):
        if self.but_light:
            if self.mapped_parameter() is None:
                self.but_light.send_value(0)
            else:
                self.but_light.enabled = True
                mp = self.mapped_parameter()
                self.but_light.send_value(value2color(mp.value, mp.min, mp.max))

    def connect_to(self, parameter):
        super(EncoderElement, self).connect_to(parameter)

        # Additional logic related to your private parameter
        self._set_lightval()
