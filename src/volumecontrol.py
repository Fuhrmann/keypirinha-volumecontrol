import keypirinha as kp
import keypirinha_util as kpu
from keypirinha_util import kwargs_encode, kwargs_decode
import re
import json

from .lib.audio import IAudioEndpointVolume, IMMDeviceEnumerator


class VolumeControl(kp.Plugin):
    # The itemcategory of the suggestions of this package
    KEYWORD = "vol"

    # The itemcategory of the suggestions of this package
    VOLUME_SUGGESTION = kp.ItemCategory.USER_BASE + 1

    # Target used to set the volume
    TARGET_SETVOLUME = "volume:set"

    def __init__(self):
        super().__init__()
        self.volume_control = IAudioEndpointVolume.get_default()

    def on_catalog(self):
        self.merge_catalog([
            self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label=self.get_mute_text(),
                short_desc="Mute/unmute the volume",
                target="{}:0".format(self.TARGET_SETVOLUME),
                args_hint=kp.ItemArgsHint.FORBIDDEN,
                hit_hint=kp.ItemHitHint.NOARGS
            )
        ])

    def on_suggest(self, user_input, items_chain):
        clean_user_input = user_input.lower().strip()
        desired_volume = self.search_volume_level(clean_user_input)

        if self.KEYWORD in clean_user_input or desired_volume:
            suggestions = []

            # If the user input has a number
            if desired_volume is False:
                suggestions = self.load_default_suggestions()
            else:
                suggestions.append(
                    self.create_item(
                        category=self.VOLUME_SUGGESTION,
                        label="Set volume to {}%".format(desired_volume),
                        short_desc="Set the volume",
                        target="{}:{}".format(self.TARGET_SETVOLUME, desired_volume),
                        args_hint=kp.ItemArgsHint.FORBIDDEN,
                        hit_hint=kp.ItemHitHint.IGNORE
                    )
                )

            self.set_suggestions(suggestions, kp.Match.ANY, kp.Sort.NONE)

        if not items_chain or items_chain[0].category() != kp.ItemCategory.KEYWORD:
            return

    def on_execute(self, item, action):
        if self.TARGET_SETVOLUME in item.target():
            value = item.target().split(':')
            self.set_volume_to(int(value[2]))

        self.on_catalog()

    # Set the volume
    def set_volume_to(self, new_volume):
        if new_volume == 0:
            self.set_mute()
        else:
            self.volume_control.SetMasterVolumeLevelScalar(float(new_volume / 100))
            if self.get_is_mute():
                self.set_mute()

    # Return if the sound is muted
    def get_is_mute(self):
        return self.volume_control.GetMute()

    # Get the text based on the muted state
    def get_mute_text(self):
        is_muted = self.get_is_mute()
        return "Unmute" if is_muted else "Mute"

    # Get the current volume
    def get_current_volume(self):
        volume = self.volume_control.GetMasterVolumeLevelScalar() * 100
        return int(volume)

    # Mute the volume
    def set_mute(self):
        mute_or_unmute = self.get_is_mute()
        self.volume_control.SetMute(not mute_or_unmute)

    # Search for a number in a string
    def search_volume_level(self, text):
        number = re.search(r'\d+', text)
        if number:
            number = int(number.group())
            return min(number, 100)

        return False

    # Load the default suggestions items used by this plugin.
    def load_default_suggestions(self):
        suggestions = []
        resource = self.load_text_resource('data/suggestions.json')
        json_suggestions = json.loads(resource)
        for item in json_suggestions:
            label = item['label']
            if 'method' in item:
                label = item['label'].format(getattr(self, item['method'], None)())

            suggestions.append(
                self.create_item(
                    category=self.VOLUME_SUGGESTION,
                    label=label,
                    short_desc=item['description'],
                    target=item['target'],
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.NOARGS
                )
            )

        return suggestions
