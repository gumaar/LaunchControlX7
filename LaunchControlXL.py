# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: output/Live/mac_universal_64_static/Release/python-bundle/MIDI Remote Scripts/Launch_Control_XL/LaunchControlXL.py
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 2024-10-28 20:51:30 UTC (1730148690)

from functools import partial
from itertools import chain
import Live
from _Framework import Task
from _Framework.ButtonMatrixElement import ButtonMatrixElement
from .EncoderElement import EncoderElement
from _Framework.IdentifiableControlSurface import IdentifiableControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE, MIDI_NOTE_TYPE
from _Framework.Layer import Layer
from _Framework.ModesComponent import AddLayerMode, ModesComponent
from _Framework.SessionComponent import SessionComponent
from _Framework.SliderElement import SliderElement
from _Framework.TransportComponent import TransportComponent
from _Framework.SubjectSlot import subject_slot
from _Framework.ModeSelectorComponent import ModeSelectorComponent
from .ButtonElement import ButtonElement
from .DeviceComponent import DeviceComponent, DeviceModeComponent
from .MixerComponent import MixerComponent, SEND_ROWS_COUNT
from .SkinDefault import make_biled_skin, make_default_skin
import logging
import time

NUM_TRACKS = 8
LIVE_CHANNEL = 8
PREFIX_TEMPLATE_SYSEX = (240, 0, 32, 41, 2, 17, 119)
LIVE_TEMPLATE_SYSEX = PREFIX_TEMPLATE_SYSEX = (LIVE_CHANNEL, 247)
CROSSFADER_ON = True
DEVICE_BUTTON_HOLD_TIME = 0.3
MODES_MAPPING = (0, 1)


class CustomModeSelector():
    def __init__(self, control_surface, device_button, mode_buttons):
        self._control_surface = control_surface
        self._device_button = device_button
        self._mode_buttons = mode_buttons
        self.mode = 0
        self.crossfader = CROSSFADER_ON
        self._press_time = None
        self._device_on = False


        # Set up listeners for the device button
        self._device_button.add_value_listener(self._on_device_button_press)
        self._is_device_button_pressed = False

        # Set up listeners for mode buttons
        for i, button in enumerate(self._mode_buttons):
            button.add_value_listener(lambda value, mode=i: self._on_mode_button_press(value, mode))

    def toggle_device(self):
        if self._device_on:
            self._device_button.send_value(0)
            self._device_on = False
        else:
            self._device_button.send_value(127)
            self._device_on = True

    def _on_device_button_press(self, value):
        """Handle the device button press."""
        if value > 0:  # Button pressed
            self._control_surface._mixer.set_track_select_buttons(ButtonMatrixElement())
            self._is_device_button_pressed = True
            self._light_up_mode_buttons()
            self._press_time = time.time()
        else:  # Button released
            elapsed_time = time.time() - self._press_time
            self._is_device_button_pressed = False
            self._reset_mode_buttons()
            if elapsed_time < DEVICE_BUTTON_HOLD_TIME:
                self.toggle_device()
            self._control_surface.reload()

    def _light_up_mode_buttons(self):
        """Light up the first three mode buttons."""
        for i, button in enumerate(self._mode_buttons):
            if i in MODES_MAPPING:
                if self.mode  == i:
                    button.send_value(127)
                else:
                    button.send_value(65)
            else:
                button.send_value(0)


    def _reset_mode_buttons(self):
        """Turn off the LEDs on the mode buttons."""
        for button in self._mode_buttons:
            button.send_value(0)  # Turn off the LED

    def _on_mode_button_press(self, value, mode):
        """Handle mode button press."""
        if self._is_device_button_pressed and value > 0:  # Button pressed
            self.mode = mode
            logging.info(f"Mode {self.mode} selected!")
            self._control_surface.show_message(f"Mode {self.mode} selected!")
            self._light_up_mode_buttons()



class LaunchControlXL(IdentifiableControlSurface):
    def __init__(self, c_instance, *a, **k):
        super(LaunchControlXL, self).__init__(
            *a, c_instance=c_instance, product_id_bytes=(0, 32, 41, 97), **k
        )
        self._biled_skin = make_biled_skin()
        self._default_skin = make_default_skin()
        with self.component_guard():
            self._create_controls()

        self._create_mode_selector()
        self._initialize_task = self._tasks.add(
            Task.sequence(Task.wait(1), Task.run(self._create_components))
        )
        self._initialize_task.kill()
        self.song().add_tracks_listener(self._on_tracks_changed)

    def reload(self):
        send_index = self._mixer._send_index if self._mixer else 0
        with self.component_guard():
            self._mixer = self._create_mixer(send_index)
            self._session.set_mixer(self._mixer)
            self.set_device_1_encoder()
            self.set_master_device_encoder()
            self._set_mode_1_sends()


    def on_identified(self):
        self._send_live_template()

    def _create_components(self):
        self._initialize_task.kill()
        self._disconnect_and_unregister_all_components()
        with self.component_guard():
            self._create_transport()
            self._create_mixer()
            self._session = self._create_session()
            #device = self._create_device()
            self._session.set_mixer(self._mixer)
            #self.set_device_component(device)
            self.set_device_1_encoder()
            self.set_master_device_encoder()


    def _create_mode_selector(self):
        device_button = self._pan_device_mode_button
        self._mode_selector = CustomModeSelector(self, device_button, self._select_buttons)

    def release_encoders(self, encoders):
        for encoder in encoders:
            #encoder.disconnect()
            encoder.release_parameter()

    def set_master_device_encoder(self):
        encoders = self._first_device_encoders
        if self._mode_selector.mode != 1:
            return
        self.release_encoders(encoders)
        if master_track := self.song().master_track.devices:
            device = self.song().master_track.devices[0]
            # first device parameter is on/off state... skip that
            for i in range(min(len(encoders), len(device.parameters) - 1)):
                encoders[i].connect_to(device.parameters[i+1])
        if self._mode_selector._device_on:
            self.release_encoders(self._send_encoders)
            self.release_encoders(self._send_encoder_lights)
            if selected_track := self.song().view.selected_track:
                if devices := selected_track.devices:
                    device = devices[0]
                    # TODO 14 here should instead be number of encoders
                    ind = 0
                    for button in self._send_encoders.iterbuttons():
                        ind += 1
                        button[0].connect_to(device.parameters[ind])



    def set_device_1_encoder(self):
        if self._mode_selector.mode != 0:
            return
        self.release_encoders(self._first_device_encoders)
        self.release_encoders(self._first_device_lights)
        session = self._on_session_offset_changed.subject
        start_index = session.track_offset()
        end_index = start_index + NUM_TRACKS
        for encoder, track_index in zip(self._first_device_encoders, range(start_index, end_index)):
            if track_index < len(self.song().tracks):
                track = self.song().tracks[track_index]
                if track.devices:  # Ensure the track has devices
                    first_device = track.devices[0]
                    if first_device.parameters:  # Ensure the device has parameters
                        first_parameter = first_device.parameters[1]
                        encoder_index = track_index - start_index
                        if self._mode_selector._device_on:
                            send_button_index1 = self._send_encoders.get_button(encoder_index, 1)
                            send_button_index2 = self._send_encoders.get_button(encoder_index, 0)
                            send_button_index1.connect_to(first_device.parameters[2])
                            send_button_index2.connect_to(first_device.parameters[3])

                        encoder.connect_to(first_parameter)

        # map encoders above cross fader to first 3 device params
        if master_track := self.song().master_track.devices:
            device = master_track[0]
            self._first_device_encoders[-1].connect_to(device.parameters[1])
            self._send_encoders.get_button(-1, 1).connect_to(device.parameters[2])
            self._send_encoders.get_button(-1, 0).connect_to(device.parameters[3])




    def _create_controls(self):
        def make_button(
            identifier, name, midi_type=MIDI_CC_TYPE, skin=self._default_skin
        ):
            return ButtonElement(
                True, midi_type, LIVE_CHANNEL, identifier, name=name, skin=skin
            )

        def make_button_list(identifiers, name):
            return [
                make_button(
                    identifier, f"{name}_{i+1}", MIDI_NOTE_TYPE, self._biled_skin
                )
                for i, identifier in enumerate(identifiers)
            ]

        def make_encoder(identifier, name):
            return EncoderElement(
                MIDI_CC_TYPE,
                LIVE_CHANNEL,
                identifier,
                Live.MidiMap.MapMode.absolute,
                name=name,
            )

        def make_slider(identifier, name):
            return SliderElement(MIDI_CC_TYPE, LIVE_CHANNEL, identifier, name=name)

        self._send_encoders = ButtonMatrixElement(
            rows=[
                [make_encoder(13+i, f"Top_Send_{i+1}") for i in range(8)],
                [make_encoder(29+i, f"Bottom_Send_{i+1}") for i in range(8)],
            ]
        )
        self._first_device_encoders = ButtonMatrixElement(
            rows= [
                [make_encoder(49+i, f"Pan_Device_{i+1}") for i in range(8)],
            ]
        )
        self._pan_device_encoders = ButtonMatrixElement(
            rows=[]
        )
        volume_faders = [make_slider(77+i, f"Volume_{i+1}") for i in range(8)]
        self._volume_faders7 = ButtonMatrixElement(rows=[volume_faders[0:7]])
        self._volume_faders = ButtonMatrixElement(rows=[volume_faders[0:8]])

        self._crossfader_control = make_slider(77+7, f"Crossfader")
        self._pan_device_mode_button = make_button(
            105, "Pan_Device_Mode", MIDI_NOTE_TYPE
        )
        self._mute_mode_button = make_button(106, "Mute_Mode", MIDI_NOTE_TYPE)
        self._solo_mode_button = make_button(107, "Solo_Mode", MIDI_NOTE_TYPE)
        self._arm_mode_button = make_button(108, "Arm_Mode", MIDI_NOTE_TYPE)
        self._up_button = make_button(104, "Up")
        self._down_button = make_button(105, "Down")
        self._left_button = make_button(106, "Track_Left")
        self._right_button = make_button(107, "Track_Right")
        self._select_buttons = ButtonMatrixElement(
            rows=[
                make_button_list(chain(range(41, 45), range(57, 60)), "Track_Select_%d")
            ]
        )
        self._state_buttons = ButtonMatrixElement(
            rows=[
                make_button_list(chain(range(73, 77), range(89, 92)), "Track_State_%d")
            ]
        )
        self._nudge_down = make_button(92,"Nudge_Down", MIDI_NOTE_TYPE)
        self._nudge_up = make_button(60,"Nudge_Up", MIDI_NOTE_TYPE)
        transport = TransportComponent()
        transport.set_nudge_buttons(self._nudge_up, self._nudge_down)
        self._send_encoder_lights = ButtonMatrixElement(
            rows=[
                make_button_list(
                    [13, 29, 45, 61, 77, 93, 109, 125], "Top_Send_Encoder_Light_%d"
                ),
                make_button_list(
                    [14, 30, 46, 62, 78, 94, 110, 126], "Middle_Send_Encoder_Light_%d"
                ),
            ]
        )
        self._first_device_lights = ButtonMatrixElement(
            rows=[
                make_button_list(
                    [15, 31, 47, 63, 79, 95, 111, 127], "Bottom_Send_Encoder_Light_%d"
                ),
            ]
        )
        self._pan_device_encoder_lights = self._first_device_lights
        for i in range(8):
            for j in range(SEND_ROWS_COUNT):
                self._send_encoders.get_button(i, j).but_light = self._send_encoder_lights.get_button(i,j)
        for i in range(8):
                j=0
                self._first_device_encoders.get_button(i, j).but_light = self._first_device_lights.get_button(i,j)

    def _create_transport(self):
        self._transport = TransportComponent(name="Transport",
          is_enabled=False,
          layer=Layer(nudge_up_button=(self._nudge_up),
                      nudge_down_button=(self._nudge_down)))
        self._transport.set_enabled(True)


    def _set_mode_1_sends(self):
        if self._mode_selector.mode != 1 or self._mode_selector._device_on:
            return
        self.release_encoders(self._send_encoders)
        self.release_encoders(self._send_encoder_lights)
        for i in range(SEND_ROWS_COUNT):
            if send_devices := self.song().return_tracks[i+self._mixer._send_index].devices:
                device = send_devices[0]
            # TODO fix range according to crossfader
            for j in range(min(8, len(device.parameters) - 1)):
                    self._send_encoders.get_button(j, i).connect_to(device.parameters[j+1])

    def _create_mixer(self, send_index=0):
        mixer = MixerComponent(self, NUM_TRACKS, is_enabled=True, auto_name=True)
        self._mixer = mixer
        mixer._set_send_index(send_index)
        send_encoders = ButtonMatrixElement()
        send_encoders_lights = ButtonMatrixElement()
        if self._mode_selector.mode == 0:
            if not self._mode_selector._device_on:
                send_encoders = self._send_encoders
                send_encoders_lights = self._send_encoder_lights

        mixer.layer = Layer(
            track_select_buttons=self._select_buttons,
            send_controls=send_encoders,
            next_sends_button=self._down_button,
            prev_sends_button=self._up_button,
            pan_controls=self._pan_device_encoders,
            volume_controls=self._volume_faders7,
            crossfader_control=self._crossfader_control,
            send_lights=send_encoders_lights,
            pan_lights=self._pan_device_encoder_lights,
        )
        mixer.on_send_index_changed = partial(
            self._show_controlled_sends_message, mixer
        )
        for channel_strip in map(mixer.channel_strip, range(NUM_TRACKS)):
            channel_strip.empty_color = "Mixer.NoTrack"
        mixer_modes = ModesComponent()
        mixer_modes.add_mode(
            "mute", [AddLayerMode(mixer, Layer(mute_buttons=self._state_buttons))]
        )
        mixer_modes.add_mode(
            "solo", [AddLayerMode(mixer, Layer(solo_buttons=self._state_buttons))]
        )
        mixer_modes.add_mode(
            "arm", [AddLayerMode(mixer, Layer(arm_buttons=self._state_buttons))]
        )
        mixer_modes.layer = Layer(
            mute_button=self._mute_mode_button,
            solo_button=self._solo_mode_button,
            arm_button=self._arm_mode_button,
        )
        mixer_modes.selected_mode = "mute"
        return mixer

    def _create_session(self):
        # Added num_scenes, otherwise highlight box is not enabled
        session = SessionComponent(num_tracks=NUM_TRACKS, num_scenes=2, is_enabled=True, auto_name=True, enable_skinning=True)

        # enable highlight box
        self.set_highlighting_session_component(session)
        # page_left and page_right instead of just one track
        session.layer = Layer(page_left_button=self._left_button, page_right_button=self._right_button)
        self._on_session_offset_changed.subject = session
        return session

    @subject_slot("offset")
    def _on_session_offset_changed(self):
        session = self._on_session_offset_changed.subject
        self._show_controlled_tracks_message(session)
        self.reload()

    def _on_tracks_changed(self):
        self.reload()

    def _show_controlled_sends_message(self, mixer):
        if mixer.send_index is not None:
            send_index = mixer.send_index
            send_name1 = chr(ord("A") + send_index)
            if send_index +1 < mixer.num_sends:
                send_name2 = chr(ord("A") + send_index + 1)
                self.show_message(f"Controlling Send {send_name1} and {send_name2}")
            else:
                self.show_message("Controlling Send %s" % send_name1)

    def _show_controlled_tracks_message(self, session):
        start = session.track_offset()
        end = min(start / 8, len(session.tracks_to_use()))
        start = start * 1
        if start < end:
            self.show_message("Controlling Track %d to %d" % (start, end))
        else:  # inserted
            self.show_message("Controlling Track %d" % start)

    def _send_live_template(self):
        self._send_midi(LIVE_TEMPLATE_SYSEX)
        self._initialize_task.restart()

    def handle_sysex(self, midi_bytes):
        if midi_bytes[:7] == PREFIX_TEMPLATE_SYSEX:
            if midi_bytes[7] == LIVE_CHANNEL:
                if self._initialize_task.is_running:
                    self._create_components()
                else:  # inserted
                    self.update()
        else:  # inserted
            super(LaunchControlXL, self).handle_sysex(midi_bytes)
