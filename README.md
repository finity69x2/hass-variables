# hass-variables

A Home Assistant component to declare and set/update variables (state).

Since rogro82 seems to have abandoned his repository and his custom_component is really useful I just forked it and updated it so it's still works with ^2021.9.0!

## Install

### Manually

Copy `variable` folder in to your home-assistant `custom_components` folder

### Automatically with HACS

This card is available in [HACS](https://github.com/custom-components/hacs) (Home Assistant Community Store)

1. In the HACS store click on Integrations and then click on the plus in the right bottom corner. Search for hass-variables click on it and then click on INSTALL THIS REPOSITORY IN HACS.
2. Restart Home Assistant.

Then the `variable` custom component will be installable through HACS and you will be able to follow the future updates.

## Configure

Add the component `variable` to your configuration and declare the variables you want.

### Example configuration

```yaml
variable:
  countdown_timer:
    value: 30
    attributes:
      friendly_name: 'Countdown'
      icon: mdi:alarm
  countdown_trigger:
    name: Countdown
    value: False
  light_scene:
    value: 'normal'
    attributes:
      previous: ''
    restore: true
  current_power_usage:
    force_update: true
```

A variable 'should' have a __value__ and can optionally have a __name__ and __attributes__, which can be used to specify additional values but can also be used to set internal attributes like icon, friendly_name etc.

In case you want your variable to restore its value and attributes after restarting you can set __restore__ to true.

In case you want your variable to update (and add a history entry) even if the value has not changed, you can set __force_update__ to true.

## Set variables from automations

To update a variables value and/or its attributes you can use the service call `variable.set_variable`

The following parameters can be used with this service:

- __variable: string (required)__
The name of the variable to update
- __value: any (optional)__
New value to set
- __attributes: dictionary (optional)__
Attributes to set or update
- __replace_attributes: boolean ( optional )__
Replace or merge current attributes (default false = merge)

### Example service calls

```yaml
action:
  - service: variable.set_variable
    data:
      variable: test_timer
      value: 30

action:
  - service: variable.set_variable
    data:
      variable: last_motion
      value: "livingroom"
      attributes:
          history_1: "{{states('variable.last_motion')}}"
          history_2: "{{state_attr('variable.last_motion','history_1')}}"
          history_3: "{{state_attr('variable.last_motion','history_2')}}"
```

### Example timer automation

```yaml
variable:
  test_timer:
    value: 0
    attributes:
      icon: mdi:alarm

script:
  schedule_test_timer:
    sequence:
      - service: variable.set_variable
        data:
          variable: test_timer
          value: 30
      - service: automation.turn_on
        data:
          entity_id: automation.test_timer_countdown

automation:
  - alias: test_timer_countdown
    initial_state: 'off'
    trigger:
      - platform: time_pattern
        seconds: '/1'
    action:
      - service: variable.set_variable
        data:
          variable: test_timer
          value: >
            {{ [((states('variable.test_timer') | int(default=0)) - 1), 0] | max }}

  - alias: test_timer_trigger
    trigger:
      platform: state
      entity_id: variable.test_timer
      to: '0'
    action:
      - service: automation.turn_off
        data:
          entity_id: automation.test_timer_countdown
```

### Play and Save TTS Messages + Message History - Made by https://github.com/jazzyisj

This is more or less an answering machine (remember those?) for your TTS messages. When you play a TTS message that you want saved under certain condtions (ie. nobody is home), you will call the script Play or Save TTS Messsage script.play_or_save_message instead of calling your tts service (or Alexa notify) directly. The script will decide whether to play the message immediately, or save it based on the conditions you specify. If a saved tts message is repeated another message is not saved, only the timestamp is updated to the most recent instance.

Messages are played back using the Play Saved TTS Messages script script.play_saved_tts_messages. Set an appropriate trigger (for example when you arrive home) in the automation Play Saved Messages automation.play_saved_messages automation to call this script automatically.

Saved messages will survive restarts.

BONUS - OPTIONAL TTS MESSAGE HISTORY

You can find the full documentation on how to do this and andjust this to your needs in here. [here](https://github.com/Wibias/hass-variables/tree/master/examples/save-tts-message/tts.md).

---

More examples can be found in the examples folder.
