# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: output/Live/mac_universal_64_static/Release/python-bundle/MIDI Remote Scripts/Launch_Control_XL/ButtonElement.py
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2024-08-12 14:49:06 UTC (1723474146)

from _Framework.ButtonElement import OFF_VALUE, ON_VALUE
from _Framework.ButtonElement import ButtonElement as ButtonElementBase

from _Framework.ButtonElement import Color

import logging

def get_next(was):
    if was == 'A':
        return 'B'
    if was == 'B':
        return 'Off'
    if was == 'Off':
        return 'A'

cross_color = {
        None: 0,
        'Off': 28,
        'A': 59,
        'B': 78
        }



class ButtonElement(ButtonElementBase):
    _on_value = None
    _off_value = None
    cur_val = None

    def reset(self):
        self._on_value = None
        self._off_value = None
        super(ButtonElement, self).reset()

    def set_on_off_values(self, on_value, off_value):
        self._on_value = on_value
        self._off_value = off_value

    def receive_value(self, value):
        super().receive_value(value)

    def send_value(self, value, **k):
        if self._on_value and 'Crossfade' in self._on_value:
            if type(value) is int:
                pass
            else:
                if value.midi_value == 0:
                    self.cur_val = 'Off'
                else:
                    if self.cur_val:
                        self.cur_val = get_next(self.cur_val)
                Color(cross_color[self.cur_val]).draw(self)

            if value is ON_VALUE and self._on_value is not None:
                if 'Crossfade' not in self._on_value:
                    self._skin[self._on_value].draw(self)
            elif value is OFF_VALUE and self._off_value is not None:
                if 'Crossfade' not in self._on_value:
                    self._skin[self._off_value].draw(self)
            else:
                super(ButtonElement, self).send_value(value, **k)
        else:
            if value is ON_VALUE and self._on_value is not None:
                self._skin[self._on_value].draw(self)
            elif value is OFF_VALUE and self._off_value is not None:
                self._skin[self._off_value].draw(self)
            else:
                super(ButtonElement, self).send_value(value, **k)
        return
