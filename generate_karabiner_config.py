#!/usr/bin/env python3
"""
Generate a Karabiner-Elements complex_modifications asset for ARTSEY.

The generated asset exposes separate left-hand and right-hand ARTSEY rules:

Left-hand physical block:
  q w e r
  a s d f

Left-hand base output:
  q->s  w->t  e->r  r->a
  a->o  s->i  d->y  f->e

Right-hand physical block:
  u i o p
  j k l ;

Right-hand base output:
  u->a  i->r  o->t  p->s
  j->e  k->y  l->i  ;->o

The default output is a minified `artsey_complex_modifications.json` asset for
Karabiner's `assets/complex_modifications` directory.
"""

from __future__ import annotations

import argparse
import copy
import json
from itertools import product
from itertools import permutations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


class ArtseyLeftKarabinerGenerator:
    """Build the shared ARTSEY rule set and export it as a Karabiner asset."""

    NUMBER_LAYER_VAR = "artsey_layer_numbers"
    NUMBER_LAYER_SHIFTED_VAR = "artsey_layer_numbers_shifted"
    NAV_LAYER_VAR = "artsey_layer_nav"
    NAV_LOCK_VAR = "artsey_lock_nav"
    MOUSE_LOCK_VAR = "artsey_lock_mouse"
    BRACKET_LAYER_VAR = "artsey_layer_brackets"
    CUSTOM_LAYER_VAR = "artsey_layer_custom"
    MEDIA_LAYER_VAR = "artsey_layer_media"
    FINGER_TOTAL_VAR = "multitouch_extension_finger_count_total"
    MANUAL_ARTSEY_VAR = "artsey_manual_enabled"
    SHIFT_LOCK_VAR = "artsey_shift_lock"
    SHIFT_ONCE_VAR = "artsey_shift_once"
    MODIFIER_STATE_VAR = "artsey_modifier_state"
    CTRL_LOCK_MASK = 1
    GUI_LOCK_MASK = 2
    ALT_LOCK_MASK = 4
    RULE_NAME = "ARTSEY Left"
    MANUAL_TOGGLE_PHYSICAL = ["z", "x", "c", "v"]
    HOLD_LAYER_THRESHOLD_MS = 120
    PROFILE_NAME = "ARTSEY"
    ASSET_TITLE = "ARTSEY (Enable Left/Right. 2 fingers = ARTSEY, 3 fingers = NAV)"

    def __init__(
        self,
        activation_conditions: List[Dict[str, Any]] | None = None,
        output_modifier_conditions: List[Dict[str, Any]] | None = None,
        output_modifiers: List[str] | None = None,
    ) -> None:
        self.activation_conditions = activation_conditions or self.two_finger_activation_conditions()
        self.output_modifier_conditions = output_modifier_conditions or []
        self.output_modifiers = output_modifiers or []

    # Canonical ARTSEY key names mapped to physical keyboard keys.
    CANONICAL_TO_PHYSICAL = {
        "a": "r",
        "r": "e",
        "t": "w",
        "s": "q",
        "e": "f",
        "y": "d",
        "i": "s",
        "o": "a",
    }

    ALPHA_COMBOS = {
        "b": ["e", "o"],
        "c": ["e", "y"],
        "d": ["a", "r", "t"],
        "f": ["a", "r"],
        "g": ["r", "t"],
        "h": ["e", "i"],
        "j": ["t", "s"],
        "k": ["y", "o"],
        "l": ["e", "y", "i"],
        "m": ["y", "i", "o"],
        "n": ["i", "o"],
        "p": ["e", "i", "o"],
        "q": ["a", "t", "s"],
        "u": ["y", "i"],
        "v": ["r", "s"],
        "w": ["a", "s"],
        "x": ["r", "t", "s"],
        "z": ["a", "r", "t", "s"],
    }

    PUNCTUATION_COMBOS = {
        "quote": ["r", "y"],
        "comma": ["a", "y"],
        "slash": ["a", "o"],
        "exclamation": ["t", "i"],
        "period": ["a", "i"],
        "question": ["s", "o"],
    }

    EDITING_COMBOS = {
        "return_or_enter": ["a", "e"],
        "tab": ["a", "r", "t", "o"],
        "delete_or_backspace": ["r", "e"],
        "delete_forward": ["r", "i"],
        "escape": ["a", "r", "o"],
    }

    NUMBER_LAYER_TAP_CANONICALS = {
        "t": "3",
        "r": "2",
        "a": "1",
        "i": "6",
        "y": "5",
        "e": "4",
    }

    NUMBER_LAYER_COMBOS = {
        "7": ["a", "r"],
        "8": ["r", "t"],
        "0": ["y", "i"],
        "9": ["e", "y"],
    }

    CUSTOM_LAYER_TAP_CANONICALS = {
        "s": "backslash",
        "t": "semicolon",
        "r": "grave_accent_and_tilde",
        "a": "number_sign",
        "o": "equal_sign",
        "i": "hyphen",
        "y": "at_sign",
    }
    MEDIA_LAYER_TAP_CANONICALS = {
        "t": "volume_increment",
        "r": "mute",
        "a": "play_or_pause",
        "i": "volume_decrement",
        "y": "scan_previous_track",
        "e": "scan_next_track",
    }
    BRACKET_LAYER_TAP_SPECS = {
        "s": ("open_bracket", True),
        "t": ("open_bracket", False),
        "r": ("9", True),
        "o": ("close_bracket", True),
        "i": ("close_bracket", False),
        "y": ("0", True),
    }

    LOCK_NAV_COMBO = ["r", "i", "e"]
    LOCK_MOUSE_COMBO = ["t", "a", "y"]
    MOUSE_LOCK_ACCEL_THRESHOLD_MS = 350
    MOUSE_LOCK_ACCEL_MULTIPLIER = 3.0
    NAV_LAYER_TAP_CANONICALS = {
        "s": "page_up",
        "t": "home",
        "r": "up_arrow",
        "a": "end",
        "i": "left_arrow",
        "y": "down_arrow",
        "e": "right_arrow",
    }
    NAV_LOCK_TAP_CANONICALS = {
        "s": "page_up",
        "t": "home",
        "r": "up_arrow",
        "a": "end",
        "o": "page_down",
        "i": "left_arrow",
        "y": "down_arrow",
        "e": "right_arrow",
    }
    MOUSE_LOCK_TAP_CANONICALS = {
        "s": {"mouse_key": {"vertical_wheel": -32}},
        "t": {"pointing_button": "button2"},
        "r": {"mouse_key": {"y": -1536}},
        "a": {"pointing_button": "button1"},
        "o": {"mouse_key": {"vertical_wheel": 32}},
        "i": {"mouse_key": {"x": -1536}},
        "y": {"mouse_key": {"y": 1536}},
        "e": {"mouse_key": {"x": 1536}},
    }
    SHIFT_LOCK_CANONICAL = ["o", "i", "y", "a"]
    SHIFT_ONCE_CANONICAL = ["s", "t", "r", "e"]
    CTRL_LOCK_CANONICAL = ["s", "e"]
    GUI_LOCK_CANONICAL = ["s", "y"]
    ALT_LOCK_CANONICAL = ["s", "i"]

    OUTPUT_ACTION_OVERRIDES = {
        "exclamation": {"key_code": "1", "modifiers": ["left_shift"]},
        "question": {"key_code": "slash", "modifiers": ["left_shift"]},
        "number_sign": {"key_code": "3", "modifiers": ["left_shift"]},
        "at_sign": {"key_code": "2", "modifiers": ["left_shift"]},
        "volume_increment": {"consumer_key_code": "volume_increment"},
        "volume_decrement": {"consumer_key_code": "volume_decrement"},
        "mute": {"consumer_key_code": "mute"},
        "play_or_pause": {"consumer_key_code": "play_or_pause"},
        "scan_previous_track": {"consumer_key_code": "scan_previous_track"},
        "scan_next_track": {"consumer_key_code": "scan_next_track"},
    }
    BROWSER_BUNDLE_IDENTIFIERS = [
        "^com\\.apple\\.Safari$",
        "^com\\.google\\.Chrome$",
        "^com\\.google\\.Chrome\\.canary$",
        "^org\\.mozilla\\.firefox$",
        "^company\\.thebrowser\\.Browser$",
        "^com\\.microsoft\\.edgemac$",
        "^com\\.brave\\.Browser$",
        "^com\\.vivaldi\\.Vivaldi$",
        "^com\\.opera\\.Opera$",
        "^com\\.kagi\\.orion$",
    ]

    SHIFTABLE_OUTPUT_KEYS = {
        *list("abcdefghijklmnopqrstuvwxyz"),
        *list("0123456789"),
        "tab",
        "page_up",
        "page_down",
        "home",
        "end",
        "up_arrow",
        "down_arrow",
        "left_arrow",
        "right_arrow",
        "comma",
        "period",
        "slash",
        "quote",
        "semicolon",
        "hyphen",
        "equal_sign",
        "open_bracket",
        "close_bracket",
        "backslash",
        "grave_accent_and_tilde",
    }

    def translate_combo(self, canonical_keys: Iterable[str]) -> List[str]:
        return [self.CANONICAL_TO_PHYSICAL[key] for key in canonical_keys]

    def physical_for_canonical(self, canonical_key: str) -> str:
        return self.CANONICAL_TO_PHYSICAL[canonical_key]

    def custom_layer_combo(self, canonical_keys: Iterable[str]) -> List[str]:
        return self.translate_combo(key for key in canonical_keys if key != "e")

    def base_taps(self) -> Dict[str, str]:
        return {
            self.physical_for_canonical(canonical_key): canonical_key
            for canonical_key in ("s", "t", "r", "a", "o", "i", "y", "e")
        }

    def number_layer_taps(self) -> Dict[str, str]:
        return {
            self.physical_for_canonical(canonical_key): output_key
            for canonical_key, output_key in self.NUMBER_LAYER_TAP_CANONICALS.items()
        }

    def nav_layer_taps(self) -> Dict[str, str]:
        return {
            self.physical_for_canonical(canonical_key): output_key
            for canonical_key, output_key in self.NAV_LAYER_TAP_CANONICALS.items()
        }

    def nav_lock_taps(self) -> Dict[str, str]:
        return {
            self.physical_for_canonical(canonical_key): output_key
            for canonical_key, output_key in self.NAV_LOCK_TAP_CANONICALS.items()
        }

    def mouse_lock_taps(self) -> Dict[str, Dict[str, Any]]:
        return {
            self.physical_for_canonical(canonical_key): copy.deepcopy(output_action)
            for canonical_key, output_action in self.MOUSE_LOCK_TAP_CANONICALS.items()
        }

    def custom_layer_taps(self) -> Dict[str, str]:
        return {
            self.physical_for_canonical(canonical_key): output_key
            for canonical_key, output_key in self.CUSTOM_LAYER_TAP_CANONICALS.items()
        }

    def media_layer_taps(self) -> Dict[str, str]:
        return {
            self.physical_for_canonical(canonical_key): output_key
            for canonical_key, output_key in self.MEDIA_LAYER_TAP_CANONICALS.items()
        }

    def bracket_layer_taps(self) -> Dict[str, tuple[str, bool]]:
        return {
            self.physical_for_canonical(canonical_key): spec
            for canonical_key, spec in self.BRACKET_LAYER_TAP_SPECS.items()
        }

    def combo_threshold(self, combo_size: int) -> int:
        return 100

    def two_finger_activation_conditions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "variable_unless",
                "name": self.MANUAL_ARTSEY_VAR,
                "value": 1,
            },
            {
                "type": "variable_if",
                "name": self.FINGER_TOTAL_VAR,
                "value": 2,
            }
        ]

    def three_finger_nav_activation_conditions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "variable_unless",
                "name": self.MANUAL_ARTSEY_VAR,
                "value": 1,
            },
            {
                "type": "variable_if",
                "name": self.FINGER_TOTAL_VAR,
                "value": 3,
            }
        ]

    def manual_activation_conditions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "variable_if",
                "name": self.MANUAL_ARTSEY_VAR,
                "value": 1,
            }
        ]

    def activation_only_conditions(self) -> List[Dict[str, Any]]:
        return list(self.activation_conditions)

    def artsey_enabled_conditions(self) -> List[Dict[str, Any]]:
        return self.activation_only_conditions() + [
            {
                "type": "variable_unless",
                "name": self.NAV_LAYER_VAR,
                "value": 1,
            },
            {
                "type": "variable_unless",
                "name": self.NAV_LOCK_VAR,
                "value": 1,
            },
            {
                "type": "variable_unless",
                "name": self.MOUSE_LOCK_VAR,
                "value": 1,
            },
            {
                "type": "variable_unless",
                "name": self.BRACKET_LAYER_VAR,
                "value": 1,
            },
            {
                "type": "variable_unless",
                "name": self.CUSTOM_LAYER_VAR,
                "value": 1,
            },
            {
                "type": "variable_unless",
                "name": self.MEDIA_LAYER_VAR,
                "value": 1,
            },
        ]

    def with_artsey_enabled_condition(self, manipulator: Dict[str, Any]) -> Dict[str, Any]:
        manipulator["conditions"] = self.artsey_enabled_conditions()
        return manipulator

    def nav_lock_conditions(self) -> List[Dict[str, Any]]:
        return self.nav_lock_activation_conditions()

    def nav_lock_activation_conditions(self) -> List[Dict[str, Any]]:
        return self.activation_only_conditions() + [
            {
                "type": "variable_if",
                "name": self.NAV_LOCK_VAR,
                "value": 1,
            },
        ]

    def mouse_lock_conditions(self) -> List[Dict[str, Any]]:
        return self.mouse_lock_activation_conditions()

    def mouse_lock_activation_conditions(self) -> List[Dict[str, Any]]:
        return self.activation_only_conditions() + [
            {
                "type": "variable_if",
                "name": self.MOUSE_LOCK_VAR,
                "value": 1,
            },
        ]

    def nav_layer_conditions(self) -> List[Dict[str, Any]]:
        return self.nav_layer_activation_conditions()

    def custom_layer_conditions(self) -> List[Dict[str, Any]]:
        return self.activation_only_conditions() + [
            {
                "type": "variable_if",
                "name": self.CUSTOM_LAYER_VAR,
                "value": 1,
            },
        ]

    def media_layer_conditions(self) -> List[Dict[str, Any]]:
        return self.activation_only_conditions() + [
            {
                "type": "variable_if",
                "name": self.MEDIA_LAYER_VAR,
                "value": 1,
            },
        ]

    def browser_media_layer_conditions(self) -> List[Dict[str, Any]]:
        return self.media_layer_conditions() + [
            {
                "type": "frontmost_application_if",
                "bundle_identifiers": self.BROWSER_BUNDLE_IDENTIFIERS,
            }
        ]

    def bracket_layer_conditions(self) -> List[Dict[str, Any]]:
        return self.activation_only_conditions() + [
            {
                "type": "variable_if",
                "name": self.BRACKET_LAYER_VAR,
                "value": 1,
            },
        ]

    def custom_layer_activation_conditions(self) -> List[Dict[str, Any]]:
        return self.activation_only_conditions() + [
            {
                "type": "variable_if",
                "name": self.CUSTOM_LAYER_VAR,
                "value": 1,
            },
        ]

    def custom_layer_shift_lock_conditions(self) -> List[Dict[str, Any]]:
        return self.custom_layer_conditions() + [
            {
                "type": "variable_if",
                "name": self.SHIFT_LOCK_VAR,
                "value": 1,
            }
        ]

    def custom_layer_shift_once_conditions(self) -> List[Dict[str, Any]]:
        return self.custom_layer_conditions() + [
            {
                "type": "variable_unless",
                "name": self.SHIFT_LOCK_VAR,
                "value": 1,
            },
            {
                "type": "variable_if",
                "name": self.SHIFT_ONCE_VAR,
                "value": 1,
            },
        ]

    def nav_layer_activation_conditions(self) -> List[Dict[str, Any]]:
        if any(
            condition.get("type") == "variable_if"
            and condition.get("name") == self.FINGER_TOTAL_VAR
            and condition.get("value") == 3
            for condition in self.activation_conditions
        ):
            return self.activation_only_conditions()
        return self.activation_only_conditions() + [
            {
                "type": "variable_if",
                "name": self.NAV_LAYER_VAR,
                "value": 1,
            },
        ]

    def nav_lock_shift_lock_conditions(self) -> List[Dict[str, Any]]:
        return self.nav_lock_conditions() + [
            {
                "type": "variable_if",
                "name": self.SHIFT_LOCK_VAR,
                "value": 1,
            }
        ]

    def nav_lock_shift_once_conditions(self) -> List[Dict[str, Any]]:
        return self.nav_lock_conditions() + [
            {
                "type": "variable_unless",
                "name": self.SHIFT_LOCK_VAR,
                "value": 1,
            },
            {
                "type": "variable_if",
                "name": self.SHIFT_ONCE_VAR,
                "value": 1,
            },
        ]

    def nav_layer_shift_lock_conditions(self) -> List[Dict[str, Any]]:
        return self.nav_layer_conditions() + [
            {
                "type": "variable_if",
                "name": self.SHIFT_LOCK_VAR,
                "value": 1,
            }
        ]

    def nav_layer_shift_once_conditions(self) -> List[Dict[str, Any]]:
        return self.nav_layer_conditions() + [
            {
                "type": "variable_unless",
                "name": self.SHIFT_LOCK_VAR,
                "value": 1,
            },
            {
                "type": "variable_if",
                "name": self.SHIFT_ONCE_VAR,
                "value": 1,
            },
        ]

    def shift_lock_conditions(self) -> List[Dict[str, Any]]:
        return self.artsey_enabled_conditions() + [
            {
                "type": "variable_if",
                "name": self.SHIFT_LOCK_VAR,
                "value": 1,
            },
        ]

    def shift_once_conditions(self) -> List[Dict[str, Any]]:
        return self.artsey_enabled_conditions() + [
            {
                "type": "variable_unless",
                "name": self.SHIFT_LOCK_VAR,
                "value": 1,
            },
            {
                "type": "variable_if",
                "name": self.SHIFT_ONCE_VAR,
                "value": 1,
            },
        ]

    def number_layer_conditions(self) -> List[Dict[str, Any]]:
        return self.artsey_enabled_conditions() + [
            {
                "type": "variable_if",
                "name": self.NUMBER_LAYER_VAR,
                "value": 1,
            },
            {
                "type": "variable_if",
                "name": self.NUMBER_LAYER_SHIFTED_VAR,
                "value": 0,
            },
            {
                "type": "variable_unless",
                "name": self.SHIFT_LOCK_VAR,
                "value": 1,
            },
            {
                "type": "variable_unless",
                "name": self.SHIFT_ONCE_VAR,
                "value": 1,
            },
        ]

    def shifted_number_layer_conditions(self) -> List[Dict[str, Any]]:
        return self.artsey_enabled_conditions() + [
            {
                "type": "variable_if",
                "name": self.NUMBER_LAYER_VAR,
                "value": 1,
            },
            {
                "type": "variable_if",
                "name": self.NUMBER_LAYER_SHIFTED_VAR,
                "value": 1,
            }
        ]

    def number_layer_shift_lock_conditions(self) -> List[Dict[str, Any]]:
        return self.artsey_enabled_conditions() + [
            {
                "type": "variable_if",
                "name": self.NUMBER_LAYER_VAR,
                "value": 1,
            },
            {
                "type": "variable_if",
                "name": self.SHIFT_LOCK_VAR,
                "value": 1,
            },
        ]

    def number_layer_shift_once_conditions(self) -> List[Dict[str, Any]]:
        return self.artsey_enabled_conditions() + [
            {
                "type": "variable_if",
                "name": self.NUMBER_LAYER_VAR,
                "value": 1,
            },
            {
                "type": "variable_unless",
                "name": self.SHIFT_LOCK_VAR,
                "value": 1,
            },
            {
                "type": "variable_if",
                "name": self.SHIFT_ONCE_VAR,
                "value": 1,
            },
        ]

    def clear_shift_once_action(self) -> Dict[str, Any]:
        return {
            "set_variable": {
                "name": self.SHIFT_ONCE_VAR,
                "value": 0,
            }
        }

    def modifier_lock_var_names(self) -> List[str]:
        return [
            self.SHIFT_LOCK_VAR,
            self.SHIFT_ONCE_VAR,
            self.MODIFIER_STATE_VAR,
        ]

    def clear_modifier_lock_actions(self) -> List[Dict[str, Any]]:
        return [
            {"set_variable": {"name": var_name, "value": 0}}
            for var_name in self.modifier_lock_var_names()
        ]

    def clear_shared_modifier_lock_actions(self) -> List[Dict[str, Any]]:
        return []

    def clear_all_modifier_lock_actions(self) -> List[Dict[str, Any]]:
        return self.clear_modifier_lock_actions() + self.clear_shared_modifier_lock_actions()

    def with_number_layer_condition(self, manipulator: Dict[str, Any]) -> Dict[str, Any]:
        manipulator["conditions"] = self.number_layer_conditions()
        return manipulator

    def with_shifted_number_layer_condition(self, manipulator: Dict[str, Any]) -> Dict[str, Any]:
        manipulator["conditions"] = self.shifted_number_layer_conditions()
        return manipulator

    def artsey_manual_notification_action(self, text: str) -> Dict[str, Any]:
        return {
            "set_notification_message": {
                "id": "artsey_manual_mode",
                "text": text,
            }
        }

    def create_manual_toggle_rule(self) -> Dict[str, Any]:
        return self.build_rule(
            "ARTSEY - Manual toggle",
            [
                self.create_state_combo_manipulator(
                    self.MANUAL_TOGGLE_PHYSICAL,
                    [
                        {
                            "set_variable": {
                                "name": self.MANUAL_ARTSEY_VAR,
                                "value": 0,
                            }
                        },
                        self.artsey_manual_notification_action(""),
                        {"key_code": "vk_none"},
                    ],
                    extra_conditions=[
                        {
                            "type": "variable_if",
                            "name": self.MANUAL_ARTSEY_VAR,
                            "value": 1,
                        }
                    ],
                    threshold_milliseconds=250,
                    detect_key_down_uninterruptedly=False,
                ),
                self.create_state_combo_manipulator(
                    self.MANUAL_TOGGLE_PHYSICAL,
                    [
                        {
                            "set_variable": {
                                "name": self.MANUAL_ARTSEY_VAR,
                                "value": 1,
                            }
                        },
                        self.artsey_manual_notification_action("ARTSEY"),
                        {"key_code": "vk_none"},
                    ],
                    extra_conditions=[
                        {
                            "type": "variable_unless",
                            "name": self.MANUAL_ARTSEY_VAR,
                            "value": 1,
                        }
                    ],
                    threshold_milliseconds=250,
                    detect_key_down_uninterruptedly=False,
                ),
            ],
        )

    def create_output_action(self, output_key: str, shifted: bool = False) -> Dict[str, Any]:
        action = dict(self.OUTPUT_ACTION_OVERRIDES.get(output_key, {"key_code": output_key}))
        modifiers = list(action.get("modifiers", []))
        if shifted and output_key in self.SHIFTABLE_OUTPUT_KEYS:
            if "left_shift" not in modifiers:
                modifiers.append("left_shift")
        if modifiers:
            action["modifiers"] = modifiers
        return action

    def modifier_lock_sources(self) -> List[tuple[int, str]]:
        return [
            (self.CTRL_LOCK_MASK, "left_control"),
            (self.GUI_LOCK_MASK, "left_command"),
            (self.ALT_LOCK_MASK, "left_option"),
        ]

    def create_output_action_variants(self, base_action: Dict[str, Any]) -> List[Dict[str, Any]]:
        variants: List[Dict[str, Any]] = []
        sources = self.modifier_lock_sources()
        for modifier_state in range(1 << len(sources)):
            action = copy.deepcopy(base_action)
            modifiers = list(action.get("modifiers", []))
            for mask, modifier_name in sources:
                if modifier_state & mask and modifier_name not in modifiers:
                    modifiers.append(modifier_name)
            if modifiers:
                action["modifiers"] = modifiers
            action["conditions"] = [
                {
                    "type": "variable_if",
                    "name": self.MODIFIER_STATE_VAR,
                    "value": modifier_state,
                }
            ]
            variants.append(action)
        return variants

    def create_modifier_state_toggle_actions(self, mask: int) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        for modifier_state in range(8):
            actions.append(
                {
                    "set_variable": {
                        "name": self.MODIFIER_STATE_VAR,
                        "value": modifier_state ^ mask,
                    },
                    "conditions": [
                        {
                            "type": "variable_if",
                            "name": self.MODIFIER_STATE_VAR,
                            "value": modifier_state,
                        }
                    ],
                }
            )
        return actions

    def create_output_actions(
        self,
        output_key: str,
        shifted: bool = False,
        clear_shift_once: bool = False,
    ) -> List[Dict[str, Any]]:
        actions = self.create_output_action_variants(self.create_output_action(output_key, shifted))
        if clear_shift_once:
            actions.append(self.clear_shift_once_action())
        return actions

    def create_single_tap_manipulator(
        self,
        physical_key: str,
        output_key: str,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        manipulator = {
            "type": "basic",
            "from": {
                "key_code": physical_key,
                "modifiers": {"optional": ["any"]},
            },
            "to_if_alone": self.create_output_actions(output_key, shifted, clear_shift_once),
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_physical_escape_clear_manipulators(self) -> List[Dict[str, Any]]:
        clear_action = [{"key_code": "escape"}, *self.clear_all_modifier_lock_actions()]
        manipulators = [
            {
                "type": "basic",
                "from": {
                    "key_code": "escape",
                    "modifiers": {"optional": ["any"]},
                },
                "to": clear_action,
                "conditions": self.activation_only_conditions(),
            }
        ]
        manipulators.extend(
            {
                "type": "basic",
                "from": {
                    "key_code": "escape",
                    "modifiers": {"optional": ["any"]},
                },
                "to": clear_action,
                "conditions": [
                    {
                        "type": "variable_if",
                        "name": var_name,
                        "value": 1,
                    }
                ],
            }
            for var_name in self.modifier_lock_var_names()
        )
        return manipulators

    def create_number_layer_hold_manipulator(
        self,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted_tap: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        hold_key = self.physical_for_canonical("s")
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.to_if_alone_timeout_milliseconds": 250,
                "basic.to_if_held_down_threshold_milliseconds": self.HOLD_LAYER_THRESHOLD_MS,
            },
            "from": {
                "key_code": hold_key,
                "modifiers": {"optional": ["any"]},
            },
            "to_if_held_down": [
                {
                    "set_variable": {
                        "name": self.NUMBER_LAYER_VAR,
                        "value": 1,
                    }
                },
                {
                    "set_variable": {
                        "name": self.NUMBER_LAYER_SHIFTED_VAR,
                        "value": 0,
                    }
                },
            ],
            "to_if_alone": [
                *self.create_output_actions("s", shifted_tap, clear_shift_once),
            ],
            "to_after_key_up": [
                {
                    "set_variable": {
                        "name": self.NUMBER_LAYER_VAR,
                        "value": 0,
                    }
                },
                {
                    "set_variable": {
                        "name": self.NUMBER_LAYER_SHIFTED_VAR,
                        "value": 0,
                    }
                },
            ],
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_nav_layer_hold_manipulator(
        self,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted_tap: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        hold_key = self.physical_for_canonical("o")
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.to_if_alone_timeout_milliseconds": 250,
                "basic.to_if_held_down_threshold_milliseconds": self.HOLD_LAYER_THRESHOLD_MS,
            },
            "from": {
                "key_code": hold_key,
                "modifiers": {"optional": ["any"]},
            },
            "to_if_held_down": [
                {
                    "set_variable": {
                        "name": self.NAV_LAYER_VAR,
                        "value": 1,
                    }
                },
            ],
            "to_if_alone": [
                *self.create_output_actions("o", shifted_tap, clear_shift_once),
            ],
            "to_after_key_up": [
                {
                    "set_variable": {
                        "name": self.NAV_LAYER_VAR,
                        "value": 0,
                    }
                },
            ],
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_custom_layer_hold_manipulator(
        self,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted_tap: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        hold_key = self.physical_for_canonical("e")
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.to_if_alone_timeout_milliseconds": 250,
                "basic.to_if_held_down_threshold_milliseconds": self.HOLD_LAYER_THRESHOLD_MS,
            },
            "from": {
                "key_code": hold_key,
                "modifiers": {"optional": ["any"]},
            },
            "to_if_held_down": [
                {
                    "set_variable": {
                        "name": self.CUSTOM_LAYER_VAR,
                        "value": 1,
                    }
                },
            ],
            "to_if_alone": [
                *self.create_output_actions("e", shifted_tap, clear_shift_once),
            ],
            "to_after_key_up": [
                {
                    "set_variable": {
                        "name": self.CUSTOM_LAYER_VAR,
                        "value": 0,
                    }
                },
            ],
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_bracket_layer_hold_manipulator(
        self,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted_tap: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        hold_key = self.physical_for_canonical("a")
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.to_if_alone_timeout_milliseconds": 250,
                "basic.to_if_held_down_threshold_milliseconds": self.HOLD_LAYER_THRESHOLD_MS,
            },
            "from": {
                "key_code": hold_key,
                "modifiers": {"optional": ["any"]},
            },
            "to_if_held_down": [
                {
                    "set_variable": {
                        "name": self.BRACKET_LAYER_VAR,
                        "value": 1,
                    }
                },
            ],
            "to_if_alone": [
                *self.create_output_actions("a", shifted_tap, clear_shift_once),
            ],
            "to_after_key_up": [
                {
                    "set_variable": {
                        "name": self.BRACKET_LAYER_VAR,
                        "value": 0,
                    }
                },
            ],
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_media_layer_hold_manipulator(
        self,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted_tap: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        hold_key = self.physical_for_canonical("o")
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.to_if_alone_timeout_milliseconds": 250,
                "basic.to_if_held_down_threshold_milliseconds": self.HOLD_LAYER_THRESHOLD_MS,
            },
            "from": {
                "key_code": hold_key,
                "modifiers": {"optional": ["any"]},
            },
            "to_if_held_down": [
                {
                    "set_variable": {
                        "name": self.MEDIA_LAYER_VAR,
                        "value": 1,
                    }
                },
            ],
            "to_if_alone": [
                *self.create_output_actions("o", shifted_tap, clear_shift_once),
            ],
            "to_after_key_up": [
                {
                    "set_variable": {
                        "name": self.MEDIA_LAYER_VAR,
                        "value": 0,
                    }
                },
            ],
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_number_layer_tap_manipulator(
        self,
        physical_key: str,
        output_key: str,
        shifted: bool = False,
        extra_conditions: List[Dict[str, Any]] | None = None,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        manipulator = {
            "type": "basic",
            "from": {
                "key_code": physical_key,
                "modifiers": {"optional": ["any"]},
            },
            "to": self.create_output_actions(output_key, shifted, clear_shift_once),
        }
        if extra_conditions is None:
            condition_wrapper = (
                self.with_number_layer_condition
                if not shifted
                else self.with_shifted_number_layer_condition
            )
            return condition_wrapper(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_custom_layer_tap_manipulator(
        self,
        physical_key: str,
        output_key: str,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        manipulator = {
            "type": "basic",
            "from": {
                "key_code": physical_key,
                "modifiers": {"optional": ["any"]},
            },
            "to": self.create_output_actions(output_key, shifted, clear_shift_once),
        }
        if extra_conditions is None:
            manipulator["conditions"] = self.custom_layer_conditions()
            return manipulator
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_bracket_layer_tap_manipulator(
        self,
        physical_key: str,
        output_key: str,
        shifted: bool,
        extra_conditions: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        manipulator = {
            "type": "basic",
            "from": {
                "key_code": physical_key,
                "modifiers": {"optional": ["any"]},
            },
            "to": self.create_output_actions(output_key, shifted),
        }
        if extra_conditions is None:
            manipulator["conditions"] = self.bracket_layer_conditions()
            return manipulator
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_nav_layer_tap_manipulator(
        self,
        physical_key: str,
        output_key: str,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        manipulator = {
            "type": "basic",
            "from": {
                "key_code": physical_key,
                "modifiers": {"optional": ["any"]},
            },
            "to": self.create_output_actions(output_key, shifted, clear_shift_once),
        }
        if extra_conditions is None:
            manipulator["conditions"] = self.nav_layer_conditions()
            return manipulator
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_custom_tap_manipulator(
        self,
        physical_key: str,
        to_actions: List[Dict[str, Any]],
        extra_conditions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return {
            "type": "basic",
            "from": {
                "key_code": physical_key,
                "modifiers": {"optional": ["any"]},
            },
            "conditions": extra_conditions,
            "to": to_actions,
        }

    def create_mouse_lock_tap_manipulator(
        self,
        physical_key: str,
        to_action: Dict[str, Any],
    ) -> Dict[str, Any]:
        manipulator = {
            "type": "basic",
            "from": {
                "key_code": physical_key,
                "modifiers": {"optional": ["any"]},
            },
            "conditions": self.mouse_lock_conditions(),
            "to": [to_action],
        }
        mouse_key = to_action.get("mouse_key", {})
        if "x" in mouse_key or "y" in mouse_key:
            accelerated_mouse_key = {
                axis: int(value * self.MOUSE_LOCK_ACCEL_MULTIPLIER)
                for axis, value in mouse_key.items()
                if axis in ("x", "y")
            }
            manipulator["parameters"] = {
                "basic.to_if_held_down_threshold_milliseconds": self.MOUSE_LOCK_ACCEL_THRESHOLD_MS,
            }
            manipulator["to_if_held_down"] = [
                {"mouse_key": accelerated_mouse_key},
            ]
        return manipulator

    def create_key_up_simultaneous_manipulator(
        self,
        release_order_keys: Sequence[str],
        output_key: str,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        combo_size = len(release_order_keys)
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.simultaneous_threshold_milliseconds": self.combo_threshold(combo_size),
            },
            "from": {
                "simultaneous": [{"key_code": key} for key in release_order_keys],
                "simultaneous_options": {
                    "key_down_order": "insensitive",
                    "key_up_order": "strict",
                    "key_up_when": "all",
                },
                "modifiers": {"optional": ["any"]},
            },
            "to": self.create_output_actions(output_key, shifted, clear_shift_once),
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)

        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_combo_manipulators(
        self,
        physical_keys: List[str],
        output_key: str,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted: bool = False,
        clear_shift_once: bool = False,
    ) -> List[Dict[str, Any]]:
        ordered_permutations = sorted(set(permutations(physical_keys)))
        return [
            self.create_key_up_simultaneous_manipulator(
                order,
                output_key,
                extra_conditions,
                shifted,
                clear_shift_once,
            )
            for order in ordered_permutations
        ]

    def create_direct_space_manipulator(
        self,
        extra_conditions: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.simultaneous_threshold_milliseconds": self.combo_threshold(4),
            },
            "from": {
                "simultaneous": [
                    {"key_code": key}
                    for key in self.translate_combo(["o", "i", "y", "e"])
                ],
                "simultaneous_options": {
                    "key_down_order": "insensitive",
                    "key_up_order": "insensitive",
                    "key_up_when": "all",
                },
                "modifiers": {"optional": ["any"]},
            },
            "to": [{"key_code": "spacebar"}],
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_direct_output_manipulator(
        self,
        physical_keys: List[str],
        output_key: str,
        extra_conditions: List[Dict[str, Any]] | None = None,
        clear_shift_once: bool = False,
        shifted: bool = False,
        threshold_milliseconds: int | None = None,
    ) -> Dict[str, Any]:
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.simultaneous_threshold_milliseconds": (
                    threshold_milliseconds
                    if threshold_milliseconds is not None
                    else self.combo_threshold(len(physical_keys))
                ),
            },
            "from": {
                "simultaneous": [{"key_code": key} for key in physical_keys],
                "simultaneous_options": {
                    "detect_key_down_uninterruptedly": True,
                    "key_down_order": "insensitive",
                    "key_up_order": "insensitive",
                    "key_up_when": "all",
                },
                "modifiers": {"optional": ["any"]},
            },
            "to": self.create_output_actions(output_key, shifted, clear_shift_once),
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_direct_symbol_manipulator(
        self,
        physical_keys: List[str],
        output_key: str,
        extra_conditions: List[Dict[str, Any]] | None = None,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        return self.create_direct_output_manipulator(
            physical_keys,
            output_key,
            extra_conditions,
            clear_shift_once,
        )

    def create_direct_tab_manipulator(
        self,
        physical_keys: List[str] | None = None,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        keys = physical_keys or ["a", "w", "e", "r"]
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.simultaneous_threshold_milliseconds": self.combo_threshold(len(keys)),
            },
            "from": {
                "simultaneous": [{"key_code": key} for key in keys],
                "simultaneous_options": {
                    "detect_key_down_uninterruptedly": True,
                    "key_down_order": "insensitive",
                    "key_up_order": "insensitive",
                    "key_up_when": "all",
                },
                "modifiers": {"optional": ["any"]},
            },
            "to": self.create_output_actions("tab", shifted, clear_shift_once),
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_direct_escape_manipulator(
        self,
        physical_keys: List[str] | None = None,
        extra_conditions: List[Dict[str, Any]] | None = None,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        keys = physical_keys or ["a", "e", "r"]
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.simultaneous_threshold_milliseconds": self.combo_threshold(len(keys)),
            },
            "from": {
                "simultaneous": [{"key_code": key} for key in keys],
                "simultaneous_options": {
                    "detect_key_down_uninterruptedly": True,
                    "key_down_order": "insensitive",
                    "key_up_order": "insensitive",
                    "key_up_when": "all",
                },
                "modifiers": {"optional": ["any"]},
            },
            "to": [{"key_code": "escape"}, *self.clear_all_modifier_lock_actions()],
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def create_state_combo_manipulator(
        self,
        physical_keys: List[str],
        to_actions: List[Dict[str, Any]],
        extra_conditions: List[Dict[str, Any]] | None = None,
        threshold_milliseconds: int | None = None,
        detect_key_down_uninterruptedly: bool = True,
    ) -> Dict[str, Any]:
        simultaneous_options = {
            "key_down_order": "insensitive",
            "key_up_order": "insensitive",
            "key_up_when": "all",
        }
        if detect_key_down_uninterruptedly:
            simultaneous_options["detect_key_down_uninterruptedly"] = True
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.simultaneous_threshold_milliseconds": (
                    threshold_milliseconds
                    if threshold_milliseconds is not None
                    else self.combo_threshold(len(physical_keys))
                ),
            },
            "from": {
                "simultaneous": [{"key_code": key} for key in physical_keys],
                "simultaneous_options": simultaneous_options,
                "modifiers": {"optional": ["any"]},
            },
            "to": to_actions,
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator

    def build_rule(self, description: str, manipulators: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {"description": description, "manipulators": manipulators}

    def build_base_tap_rule(
        self,
        description: str = "ARTSEY - Base taps",
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        base_taps = self.base_taps()
        hold_keys = {self.physical_for_canonical("s")}
        manipulators = [
            self.create_number_layer_hold_manipulator(
                extra_conditions,
                shifted_tap=shifted,
                clear_shift_once=clear_shift_once,
            ),
        ]
        if self.BRACKET_LAYER_TAP_SPECS:
            hold_keys.add(self.physical_for_canonical("a"))
            manipulators.append(
                self.create_bracket_layer_hold_manipulator(
                    extra_conditions,
                    shifted_tap=shifted,
                    clear_shift_once=clear_shift_once,
                )
            )
        if self.MEDIA_LAYER_TAP_CANONICALS:
            hold_keys.add(self.physical_for_canonical("o"))
            manipulators.append(
                self.create_media_layer_hold_manipulator(
                    extra_conditions,
                    shifted_tap=shifted,
                    clear_shift_once=clear_shift_once,
                )
            )
        if self.CUSTOM_LAYER_TAP_CANONICALS:
            hold_keys.add(self.physical_for_canonical("e"))
            manipulators.append(
                self.create_custom_layer_hold_manipulator(
                    extra_conditions,
                    shifted_tap=shifted,
                    clear_shift_once=clear_shift_once,
                )
            )
        manipulators.extend(
            self.create_single_tap_manipulator(
                physical_key,
                output_key,
                extra_conditions,
                shifted,
                clear_shift_once,
            )
            for physical_key, output_key in base_taps.items()
            if physical_key not in hold_keys
        )
        return self.build_rule(description, manipulators)

    def build_combo_rule(
        self,
        description: str,
        combos: Dict[str, List[str]],
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        combo_items = sorted(combos.items(), key=lambda item: (-len(item[1]), item[0]))
        manipulators: List[Dict[str, Any]] = []
        for output_key, canonical_combo in combo_items:
            physical_keys = self.translate_combo(canonical_combo)
            manipulators.extend(
                self.create_combo_manipulators(
                    physical_keys,
                    output_key,
                    extra_conditions,
                    shifted,
                    clear_shift_once,
                )
            )
        return self.build_rule(description, manipulators)

    def build_shift_modifier_rule(self) -> Dict[str, Any]:
        return self.build_rule(
            "ARTSEY - Shift modifiers",
            [
                *self.create_physical_escape_clear_manipulators(),
                self.create_state_combo_manipulator(
                    self.translate_combo(self.SHIFT_LOCK_CANONICAL),
                    [
                        {"set_variable": {"name": self.SHIFT_LOCK_VAR, "value": 0}},
                        {"set_variable": {"name": self.SHIFT_ONCE_VAR, "value": 0}},
                    ],
                    self.shift_lock_conditions(),
                ),
                self.create_state_combo_manipulator(
                    self.translate_combo(self.SHIFT_LOCK_CANONICAL),
                    [
                        {"set_variable": {"name": self.SHIFT_LOCK_VAR, "value": 1}},
                        {"set_variable": {"name": self.SHIFT_ONCE_VAR, "value": 0}},
                    ],
                    self.artsey_enabled_conditions() + [
                        {
                            "type": "variable_unless",
                            "name": self.SHIFT_LOCK_VAR,
                            "value": 1,
                        }
                    ],
                ),
                self.create_state_combo_manipulator(
                    self.translate_combo(self.SHIFT_ONCE_CANONICAL),
                    [
                        {"set_variable": {"name": self.SHIFT_LOCK_VAR, "value": 0}},
                        {"set_variable": {"name": self.SHIFT_ONCE_VAR, "value": 1}},
                    ],
                    detect_key_down_uninterruptedly=False,
                ),
                self.create_state_combo_manipulator(
                    self.translate_combo(self.CTRL_LOCK_CANONICAL),
                    self.create_modifier_state_toggle_actions(self.CTRL_LOCK_MASK),
                    self.artsey_enabled_conditions(),
                    threshold_milliseconds=100,
                    detect_key_down_uninterruptedly=False,
                ),
                self.create_state_combo_manipulator(
                    self.translate_combo(self.GUI_LOCK_CANONICAL),
                    self.create_modifier_state_toggle_actions(self.GUI_LOCK_MASK),
                    self.artsey_enabled_conditions(),
                    threshold_milliseconds=100,
                    detect_key_down_uninterruptedly=False,
                ),
                self.create_state_combo_manipulator(
                    self.translate_combo(self.ALT_LOCK_CANONICAL),
                    self.create_modifier_state_toggle_actions(self.ALT_LOCK_MASK),
                    self.artsey_enabled_conditions(),
                    threshold_milliseconds=100,
                    detect_key_down_uninterruptedly=False,
                ),
            ],
        )

    def nav_mode_condition_variants(self) -> List[List[Dict[str, Any]]]:
        return [
            self.nav_layer_activation_conditions(),
            self.nav_lock_activation_conditions(),
        ]

    def build_nav_mode_special_rule(self) -> Dict[str, Any]:
        manipulators: List[Dict[str, Any]] = []
        modifier_specs = [
            (self.CTRL_LOCK_MASK, self.CTRL_LOCK_CANONICAL),
            (self.GUI_LOCK_MASK, self.GUI_LOCK_CANONICAL),
            (self.ALT_LOCK_MASK, self.ALT_LOCK_CANONICAL),
        ]
        for base_conditions in self.nav_mode_condition_variants():
            manipulators.append(
                self.create_state_combo_manipulator(
                    self.translate_combo(self.SHIFT_LOCK_CANONICAL),
                    [
                        {"set_variable": {"name": self.SHIFT_LOCK_VAR, "value": 0}},
                        {"set_variable": {"name": self.SHIFT_ONCE_VAR, "value": 0}},
                    ],
                    base_conditions + [
                        {
                            "type": "variable_if",
                            "name": self.SHIFT_LOCK_VAR,
                            "value": 1,
                        }
                    ],
                )
            )
            manipulators.append(
                self.create_state_combo_manipulator(
                    self.translate_combo(self.SHIFT_LOCK_CANONICAL),
                    [
                        {"set_variable": {"name": self.SHIFT_LOCK_VAR, "value": 1}},
                        {"set_variable": {"name": self.SHIFT_ONCE_VAR, "value": 0}},
                    ],
                    base_conditions + [
                        {
                            "type": "variable_unless",
                            "name": self.SHIFT_LOCK_VAR,
                            "value": 1,
                        }
                    ],
                )
            )
            manipulators.append(
                self.create_state_combo_manipulator(
                    self.translate_combo(self.SHIFT_ONCE_CANONICAL),
                    [
                        {"set_variable": {"name": self.SHIFT_LOCK_VAR, "value": 0}},
                        {"set_variable": {"name": self.SHIFT_ONCE_VAR, "value": 1}},
                    ],
                    base_conditions,
                    detect_key_down_uninterruptedly=False,
                )
            )
            for lock_mask, canonical_combo in modifier_specs:
                physical_keys = self.translate_combo(canonical_combo)
                manipulators.append(
                    self.create_state_combo_manipulator(
                        physical_keys,
                        self.create_modifier_state_toggle_actions(lock_mask),
                        base_conditions,
                        threshold_milliseconds=100,
                        detect_key_down_uninterruptedly=False,
                    )
                )
        return self.build_rule("ARTSEY - Nav special", manipulators)

    def build_custom_layer_special_rule(self) -> Dict[str, Any]:
        base_conditions = self.custom_layer_activation_conditions()
        return self.build_rule(
            "ARTSEY - Custom special",
            [
                self.create_state_combo_manipulator(
                    self.custom_layer_combo(self.SHIFT_LOCK_CANONICAL),
                    [
                        {"set_variable": {"name": self.SHIFT_LOCK_VAR, "value": 0}},
                        {"set_variable": {"name": self.SHIFT_ONCE_VAR, "value": 0}},
                    ],
                    base_conditions + [
                        {
                            "type": "variable_if",
                            "name": self.SHIFT_LOCK_VAR,
                            "value": 1,
                        }
                    ],
                ),
                self.create_state_combo_manipulator(
                    self.custom_layer_combo(self.SHIFT_LOCK_CANONICAL),
                    [
                        {"set_variable": {"name": self.SHIFT_LOCK_VAR, "value": 1}},
                        {"set_variable": {"name": self.SHIFT_ONCE_VAR, "value": 0}},
                    ],
                    base_conditions + [
                        {
                            "type": "variable_unless",
                            "name": self.SHIFT_LOCK_VAR,
                            "value": 1,
                        }
                    ],
                ),
                self.create_state_combo_manipulator(
                    self.custom_layer_combo(self.SHIFT_ONCE_CANONICAL),
                    [
                        {"set_variable": {"name": self.SHIFT_LOCK_VAR, "value": 0}},
                        {"set_variable": {"name": self.SHIFT_ONCE_VAR, "value": 1}},
                    ],
                    base_conditions,
                    detect_key_down_uninterruptedly=False,
                ),
            ],
        )

    def build_lock_layer_rule(self) -> Dict[str, Any]:
        manipulators: List[Dict[str, Any]] = [
            self.create_state_combo_manipulator(
                self.translate_combo(self.LOCK_NAV_COMBO),
                [
                    {"set_variable": {"name": self.NAV_LOCK_VAR, "value": 0}},
                ],
                self.nav_lock_conditions() + [
                    {
                        "type": "variable_unless",
                        "name": self.MOUSE_LOCK_VAR,
                        "value": 1,
                    },
                ],
            ),
            self.create_state_combo_manipulator(
                self.translate_combo(self.LOCK_NAV_COMBO),
                [
                    {"set_variable": {"name": self.NAV_LOCK_VAR, "value": 1}},
                ],
                self.activation_only_conditions() + [
                    {
                        "type": "variable_unless",
                        "name": self.NAV_LOCK_VAR,
                        "value": 1,
                    },
                    {
                        "type": "variable_unless",
                        "name": self.MOUSE_LOCK_VAR,
                        "value": 1,
                    },
                ],
            ),
            self.create_state_combo_manipulator(
                self.translate_combo(self.LOCK_MOUSE_COMBO),
                [
                    {"set_variable": {"name": self.MOUSE_LOCK_VAR, "value": 0}},
                ],
                self.mouse_lock_conditions(),
                threshold_milliseconds=250,
                detect_key_down_uninterruptedly=False,
            ),
            self.create_state_combo_manipulator(
                self.translate_combo(self.LOCK_MOUSE_COMBO),
                [
                    {"set_variable": {"name": self.MOUSE_LOCK_VAR, "value": 1}},
                ],
                self.activation_only_conditions() + [
                    {
                        "type": "variable_unless",
                        "name": self.MOUSE_LOCK_VAR,
                        "value": 1,
                    },
                ],
                threshold_milliseconds=250,
                detect_key_down_uninterruptedly=False,
            ),
        ]
        return self.build_rule("ARTSEY - Lock layers", manipulators)

    def build_nav_mode_editing_rule(self) -> Dict[str, Any]:
        nav_editing_combos = {
            "return_or_enter": self.EDITING_COMBOS["return_or_enter"],
            "delete_or_backspace": self.EDITING_COMBOS["delete_or_backspace"],
            "delete_forward": self.EDITING_COMBOS["delete_forward"],
        }
        manipulators: List[Dict[str, Any]] = []
        for base_conditions, shift_lock_conditions, shift_once_conditions in (
            (
                self.nav_layer_conditions(),
                self.nav_layer_shift_lock_conditions(),
                self.nav_layer_shift_once_conditions(),
            ),
            (
                self.nav_lock_conditions(),
                self.nav_lock_shift_lock_conditions(),
                self.nav_lock_shift_once_conditions(),
            ),
        ):
            manipulators.append(self.create_direct_space_manipulator(base_conditions))
            manipulators.extend(
                self.build_priority_editing_rule(
                    extra_conditions=shift_lock_conditions,
                    shifted=True,
                )["manipulators"]
            )
            manipulators.extend(
                self.build_priority_editing_rule(
                    extra_conditions=shift_once_conditions,
                    shifted=True,
                    clear_shift_once=True,
                )["manipulators"]
            )
            manipulators.extend(
                self.build_priority_editing_rule(
                    extra_conditions=base_conditions,
                )["manipulators"]
            )
            manipulators.extend(
                self.build_combo_rule(
                    "ARTSEY - Nav editing combos",
                    nav_editing_combos,
                    base_conditions,
                )["manipulators"]
            )
        return self.build_rule("ARTSEY - Nav editing", manipulators)

    def build_nav_lock_output_rule(self) -> Dict[str, Any]:
        manipulators: List[Dict[str, Any]] = []
        manipulators.extend(
            self.create_number_layer_tap_manipulator(
                physical_key,
                output_key,
                shifted=True,
                extra_conditions=self.nav_lock_shift_lock_conditions(),
            )
            for physical_key, output_key in self.nav_lock_taps().items()
        )
        manipulators.extend(
            self.create_number_layer_tap_manipulator(
                physical_key,
                output_key,
                shifted=True,
                clear_shift_once=True,
                extra_conditions=self.nav_lock_shift_once_conditions(),
            )
            for physical_key, output_key in self.nav_lock_taps().items()
        )
        manipulators.extend(
            self.create_number_layer_tap_manipulator(
                physical_key,
                output_key,
                extra_conditions=self.nav_lock_conditions(),
            )
            for physical_key, output_key in self.nav_lock_taps().items()
        )
        return self.build_rule("ARTSEY - Lock layer outputs", manipulators)

    def build_mouse_lock_output_rule(self) -> Dict[str, Any]:
        manipulators: List[Dict[str, Any]] = []
        manipulators.extend(
            self.create_mouse_lock_tap_manipulator(physical_key, output_action)
            for physical_key, output_action in self.mouse_lock_taps().items()
        )
        return self.build_rule("ARTSEY - Mouse lock outputs", manipulators)

    def build_hold_nav_layer_rule(self) -> Dict[str, Any]:
        manipulators: List[Dict[str, Any]] = []
        manipulators.extend(
            self.create_nav_layer_tap_manipulator(
                physical_key,
                output_key,
                extra_conditions=self.nav_layer_shift_lock_conditions(),
                shifted=True,
            )
            for physical_key, output_key in self.nav_layer_taps().items()
        )
        manipulators.extend(
            self.create_nav_layer_tap_manipulator(
                physical_key,
                output_key,
                extra_conditions=self.nav_layer_shift_once_conditions(),
                shifted=True,
                clear_shift_once=True,
            )
            for physical_key, output_key in self.nav_layer_taps().items()
        )
        manipulators.extend(
            self.create_nav_layer_tap_manipulator(physical_key, output_key)
            for physical_key, output_key in self.nav_layer_taps().items()
        )
        return self.build_rule("ARTSEY - Hold nav layer", manipulators)

    def build_number_layer_rule(self) -> Dict[str, Any]:
        manipulators: List[Dict[str, Any]] = []
        combo_items = sorted(self.NUMBER_LAYER_COMBOS.items(), key=lambda item: (-len(item[1]), item[0]))
        for output_key, canonical_combo in combo_items:
            physical_keys = self.translate_combo(canonical_combo)
            manipulators.extend(
                self.create_combo_manipulators(
                    physical_keys,
                    output_key,
                    self.number_layer_conditions(),
                )
            )
            manipulators.extend(
                self.create_combo_manipulators(
                    physical_keys,
                    output_key,
                    self.shifted_number_layer_conditions(),
                    shifted=True,
                )
            )
            manipulators.extend(
                self.create_combo_manipulators(
                    physical_keys,
                    output_key,
                    self.number_layer_shift_lock_conditions(),
                    shifted=True,
                )
            )
            manipulators.extend(
                self.create_combo_manipulators(
                    physical_keys,
                    output_key,
                    self.number_layer_shift_once_conditions(),
                    shifted=True,
                    clear_shift_once=True,
                )
            )

        number_layer_taps = self.number_layer_taps()
        manipulators.extend(
            self.create_number_layer_tap_manipulator(physical_key, output_key)
            for physical_key, output_key in number_layer_taps.items()
        )
        manipulators.extend(
            self.create_number_layer_tap_manipulator(physical_key, output_key, shifted=True)
            for physical_key, output_key in number_layer_taps.items()
        )
        manipulators.extend(
            self.create_number_layer_tap_manipulator(
                physical_key,
                output_key,
                shifted=True,
                extra_conditions=self.number_layer_shift_lock_conditions(),
            )
            for physical_key, output_key in number_layer_taps.items()
        )
        manipulators.extend(
            self.create_number_layer_tap_manipulator(
                physical_key,
                output_key,
                shifted=True,
                extra_conditions=self.number_layer_shift_once_conditions(),
                clear_shift_once=True,
            )
            for physical_key, output_key in number_layer_taps.items()
        )

        return self.build_rule("ARTSEY - Number layer", manipulators)

    def build_number_mode_editing_rule(self) -> Dict[str, Any]:
        manipulators: List[Dict[str, Any]] = []
        manipulators.append(self.create_direct_space_manipulator(self.number_layer_conditions()))
        manipulators.append(
            self.create_direct_space_manipulator(self.shifted_number_layer_conditions())
        )
        manipulators.extend(
            self.build_priority_editing_rule(
                "ARTSEY - Number editing (Shift lock)",
                self.number_layer_shift_lock_conditions(),
                shifted=True,
            )["manipulators"]
        )
        manipulators.extend(
            self.build_priority_editing_rule(
                "ARTSEY - Number editing (Shift once)",
                self.number_layer_shift_once_conditions(),
                shifted=True,
                clear_shift_once=True,
            )["manipulators"]
        )
        manipulators.extend(
            self.build_priority_editing_rule(
                "ARTSEY - Number editing",
                self.number_layer_conditions(),
            )["manipulators"]
        )
        return self.build_rule("ARTSEY - Number editing", manipulators)

    def build_custom_layer_rule(self) -> Dict[str, Any]:
        manipulators: List[Dict[str, Any]] = []
        manipulators.extend(
            self.create_custom_layer_tap_manipulator(
                physical_key,
                output_key,
                self.custom_layer_shift_lock_conditions(),
                shifted=True,
            )
            for physical_key, output_key in self.custom_layer_taps().items()
        )
        manipulators.extend(
            self.create_custom_layer_tap_manipulator(
                physical_key,
                output_key,
                self.custom_layer_shift_once_conditions(),
                shifted=True,
                clear_shift_once=True,
            )
            for physical_key, output_key in self.custom_layer_taps().items()
        )
        manipulators.extend(
            self.create_custom_layer_tap_manipulator(physical_key, output_key)
            for physical_key, output_key in self.custom_layer_taps().items()
        )
        return self.build_rule("ARTSEY - Custom layer", manipulators)

    def build_media_layer_rule(self) -> Dict[str, Any]:
        manipulators: List[Dict[str, Any]] = []
        browser_seek_outputs = {
            "scan_previous_track": "left_arrow",
            "scan_next_track": "right_arrow",
        }
        for physical_key, output_key in self.media_layer_taps().items():
            if output_key in browser_seek_outputs:
                manipulators.append(
                    self.create_single_tap_manipulator(
                        physical_key,
                        browser_seek_outputs[output_key],
                        self.browser_media_layer_conditions(),
                    )
                )
            manipulators.append(
                self.create_single_tap_manipulator(
                    physical_key,
                    output_key,
                    self.media_layer_conditions(),
                )
            )
        return self.build_rule("ARTSEY - Media layer", manipulators)

    def build_bracket_layer_rule(self) -> Dict[str, Any]:
        return self.build_rule(
            "ARTSEY - Bracket layer",
            [
                self.create_bracket_layer_tap_manipulator(physical_key, output_key, shifted)
                for physical_key, (output_key, shifted) in self.bracket_layer_taps().items()
            ],
        )

    def build_space_rule(self) -> Dict[str, Any]:
        return self.build_rule("ARTSEY - Space", [self.create_direct_space_manipulator()])

    def build_priority_editing_rule(
        self,
        description: str = "ARTSEY - Priority editing",
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        return self.build_rule(
            description,
            [
                self.create_direct_output_manipulator(
                    self.translate_combo(self.EDITING_COMBOS["return_or_enter"]),
                    "return_or_enter",
                    extra_conditions,
                    clear_shift_once,
                    shifted,
                ),
                self.create_direct_output_manipulator(
                    self.translate_combo(self.EDITING_COMBOS["delete_or_backspace"]),
                    "delete_or_backspace",
                    extra_conditions,
                    clear_shift_once,
                    shifted,
                ),
                self.create_direct_output_manipulator(
                    self.translate_combo(self.EDITING_COMBOS["delete_forward"]),
                    "delete_forward",
                    extra_conditions,
                    clear_shift_once,
                    shifted,
                ),
                self.create_direct_tab_manipulator(
                    self.translate_combo(self.EDITING_COMBOS["tab"]),
                    extra_conditions,
                    shifted,
                    clear_shift_once,
                ),
                self.create_direct_escape_manipulator(
                    self.translate_combo(self.EDITING_COMBOS["escape"]),
                    extra_conditions,
                    clear_shift_once,
                ),
            ],
        )

    def build_priority_symbol_rule(
        self,
        description: str = "ARTSEY - Priority symbols",
        extra_conditions: List[Dict[str, Any]] | None = None,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        return self.build_rule(
            description,
            [
                self.create_direct_symbol_manipulator(
                    self.translate_combo(self.PUNCTUATION_COMBOS["exclamation"]),
                    "exclamation",
                    extra_conditions,
                    clear_shift_once,
                ),
                self.create_direct_symbol_manipulator(
                    self.translate_combo(self.PUNCTUATION_COMBOS["question"]),
                    "question",
                    extra_conditions,
                    clear_shift_once,
                ),
            ],
        )

    def generate_control_rules(self) -> List[Dict[str, Any]]:
        rules = [
            self.build_shift_modifier_rule(),
            self.build_lock_layer_rule(),
            self.build_nav_mode_special_rule(),
        ]
        if self.CUSTOM_LAYER_TAP_CANONICALS:
            rules.append(self.build_custom_layer_special_rule())
        return rules

    def generate_output_rules(self) -> List[Dict[str, Any]]:
        rules = [
            self.build_number_mode_editing_rule(),
            self.build_number_layer_rule(),
            self.build_nav_mode_editing_rule(),
            self.build_nav_lock_output_rule(),
            self.build_mouse_lock_output_rule(),
        ]
        if self.BRACKET_LAYER_TAP_SPECS:
            rules.append(self.build_bracket_layer_rule())
        if self.MEDIA_LAYER_TAP_CANONICALS:
            rules.append(self.build_media_layer_rule())
        if self.CUSTOM_LAYER_TAP_CANONICALS:
            rules.append(self.build_custom_layer_rule())
        rules.extend([
            self.build_priority_editing_rule(
                "ARTSEY - Priority editing (Shift lock)",
                self.shift_lock_conditions(),
                shifted=True,
            ),
            self.build_priority_editing_rule(
                "ARTSEY - Priority editing (Shift once)",
                self.shift_once_conditions(),
                shifted=True,
                clear_shift_once=True,
            ),
            self.build_priority_symbol_rule(
                "ARTSEY - Priority symbols (Shift lock)",
                self.shift_lock_conditions(),
            ),
            self.build_priority_symbol_rule(
                "ARTSEY - Priority symbols (Shift once)",
                self.shift_once_conditions(),
                clear_shift_once=True,
            ),
            self.build_combo_rule(
                "ARTSEY - Alpha combos (Shift lock)",
                self.ALPHA_COMBOS,
                self.shift_lock_conditions(),
                shifted=True,
            ),
            self.build_combo_rule(
                "ARTSEY - Alpha combos (Shift once)",
                self.ALPHA_COMBOS,
                self.shift_once_conditions(),
                shifted=True,
                clear_shift_once=True,
            ),
            self.build_combo_rule(
                "ARTSEY - Punctuation (Shift lock)",
                self.PUNCTUATION_COMBOS,
                self.shift_lock_conditions(),
                shifted=True,
            ),
            self.build_combo_rule(
                "ARTSEY - Punctuation (Shift once)",
                self.PUNCTUATION_COMBOS,
                self.shift_once_conditions(),
                shifted=True,
                clear_shift_once=True,
            ),
            self.build_base_tap_rule(
                "ARTSEY - Base taps (Shift lock)",
                self.shift_lock_conditions(),
                shifted=True,
            ),
            self.build_base_tap_rule(
                "ARTSEY - Base taps (Shift once)",
                self.shift_once_conditions(),
                shifted=True,
                clear_shift_once=True,
            ),
            self.build_space_rule(),
            self.build_priority_editing_rule(),
            self.build_priority_symbol_rule(),
            self.build_combo_rule("ARTSEY - Alpha combos", self.ALPHA_COMBOS),
            self.build_combo_rule("ARTSEY - Punctuation", self.PUNCTUATION_COMBOS),
            self.build_combo_rule("ARTSEY - Editing", self.EDITING_COMBOS),
            self.build_base_tap_rule(),
        ])
        return rules

    def generate_three_finger_nav_rules(self) -> List[Dict[str, Any]]:
        return [
            self.build_nav_mode_special_rule(),
            self.build_nav_mode_editing_rule(),
            self.build_hold_nav_layer_rule(),
        ]

    def merge_rules(self, description: str, rules: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        manipulators: List[Dict[str, Any]] = []
        for rule in rules:
            manipulators.extend(copy.deepcopy(rule["manipulators"]))
        return self.build_rule(description, manipulators)

    def merged_rule_for_all_activations(self) -> Dict[str, Any]:
        variants = [
            ("Manual", self.manual_activation_conditions()),
            ("Two Fingers", self.two_finger_activation_conditions()),
            ("Three Fingers Nav", self.three_finger_nav_activation_conditions()),
        ]
        all_rules: List[Dict[str, Any]] = []
        for label, activation_conditions in variants:
            base_generator = self.__class__(activation_conditions)
            if label == "Three Fingers Nav":
                variant_rules = base_generator.generate_three_finger_nav_rules()
            else:
                variant_rules = base_generator.generate_control_rules()
                output_generator = self.__class__(activation_conditions)
                variant_rules.extend(output_generator.generate_output_rules())
            all_rules.append(
                base_generator.merge_rules(
                    f"{self.RULE_NAME} ({label})",
                    variant_rules,
                )
            )
        manual_toggle_rule = self.create_manual_toggle_rule()
        return self.merge_rules(self.RULE_NAME, [manual_toggle_rule, *all_rules])

    def generate_config(self) -> Dict[str, Any]:
        rules = [
            ArtseyLeftKarabinerGenerator().merged_rule_for_all_activations(),
            ArtseyRightKarabinerGenerator().merged_rule_for_all_activations(),
        ]

        return {
            "profiles": [
                {
                    "name": self.PROFILE_NAME,
                    "selected": True,
                    "complex_modifications": {
                        "parameters": {
                            "basic.simultaneous_threshold_milliseconds": 100,
                            "basic.to_if_alone_timeout_milliseconds": 250,
                        },
                        "rules": rules,
                    },
                    "devices": [],
                    "virtual_hid_keyboard": {
                        "country_code": 0,
                        "keyboard_type_v2": "ansi",
                    },
                }
            ]
        }

    def generate_complex_modifications_asset(self) -> Dict[str, Any]:
        config = self.generate_config()
        profile = config["profiles"][0]
        asset_rules = copy.deepcopy(profile["complex_modifications"]["rules"])
        description_overrides = {
            "ARTSEY Left": "ARTSEY Left (manual toggle: zxcv)",
            "ARTSEY Right": "ARTSEY Right (manual toggle: m,./)",
        }
        for rule in asset_rules:
            description = rule.get("description")
            if description in description_overrides:
                rule["description"] = description_overrides[description]
        return {
            "title": self.ASSET_TITLE,
            "rules": asset_rules,
        }

    @staticmethod
    def write_json(path: Path, data: Dict[str, Any], minify: bool = False) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        if minify:
            text = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        else:
            text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        path.write_text(text, encoding="utf-8")
        return path

    def save_complex_modifications_asset(
        self,
        filename: str = "artsey_complex_modifications.json",
    ) -> Path:
        asset = self.generate_complex_modifications_asset()
        path = Path(filename)
        return self.write_json(path, asset, minify=True)


class ArtseyRightKarabinerGenerator(ArtseyLeftKarabinerGenerator):
    NUMBER_LAYER_VAR = "artsey_layer_numbers"
    NUMBER_LAYER_SHIFTED_VAR = "artsey_layer_numbers_shifted"
    NAV_LAYER_VAR = "artsey_layer_nav"
    NAV_LOCK_VAR = "artsey_lock_nav"
    MOUSE_LOCK_VAR = "artsey_lock_mouse"
    SHIFT_LOCK_VAR = "artsey_shift_lock"
    SHIFT_ONCE_VAR = "artsey_shift_once"
    RULE_NAME = "ARTSEY Right"
    MANUAL_TOGGLE_PHYSICAL = ["m", "comma", "period", "slash"]
    EDITING_COMBOS = {
        **ArtseyLeftKarabinerGenerator.EDITING_COMBOS,
        "delete_or_backspace": ["r", "e"],
        "delete_forward": ["r", "i"],
    }
    CANONICAL_TO_PHYSICAL = {
        "a": "u",
        "r": "i",
        "t": "o",
        "s": "p",
        "e": "j",
        "y": "k",
        "i": "l",
        "o": "semicolon",
    }
    NAV_LAYER_TAP_CANONICALS = {
        "s": "page_up",
        "t": "end",
        "r": "up_arrow",
        "a": "home",
        "i": "right_arrow",
        "y": "down_arrow",
        "e": "left_arrow",
    }
    NAV_LOCK_TAP_CANONICALS = {
        "s": "page_up",
        "t": "end",
        "r": "up_arrow",
        "a": "home",
        "o": "page_down",
        "i": "right_arrow",
        "y": "down_arrow",
        "e": "left_arrow",
    }
    MOUSE_LOCK_TAP_CANONICALS = {
        "s": {"mouse_key": {"vertical_wheel": -32}},
        "t": {"pointing_button": "button2"},
        "r": {"mouse_key": {"y": -1536}},
        "a": {"pointing_button": "button1"},
        "o": {"mouse_key": {"vertical_wheel": 32}},
        "i": {"mouse_key": {"x": 1536}},
        "y": {"mouse_key": {"y": 1536}},
        "e": {"mouse_key": {"x": -1536}},
    }
    BRACKET_LAYER_TAP_SPECS = {
        "r": ("9", True),
        "t": ("open_bracket", True),
        "s": ("open_bracket", False),
        "y": ("0", True),
        "i": ("close_bracket", False),
        "o": ("close_bracket", True),
    }
    CUSTOM_LAYER_TAP_CANONICALS = {
        "a": "number_sign",
        "r": "grave_accent_and_tilde",
        "t": "semicolon",
        "s": "backslash",
        "y": "at_sign",
        "i": "hyphen",
        "o": "equal_sign",
    }
    MEDIA_LAYER_TAP_CANONICALS = {
        "a": "play_or_pause",
        "r": "mute",
        "t": "volume_increment",
        "e": "scan_previous_track",
        "y": "scan_next_track",
        "i": "volume_decrement",
    }

    def clear_shared_modifier_lock_actions(self) -> List[Dict[str, Any]]:
        return []

    def create_bracket_layer_hold_manipulator(
        self,
        extra_conditions: List[Dict[str, Any]] | None = None,
        shifted_tap: bool = False,
        clear_shift_once: bool = False,
    ) -> Dict[str, Any]:
        hold_key = self.physical_for_canonical("a")
        manipulator = {
            "type": "basic",
            "parameters": {
                "basic.to_if_alone_timeout_milliseconds": 250,
                "basic.to_if_held_down_threshold_milliseconds": self.HOLD_LAYER_THRESHOLD_MS,
            },
            "from": {
                "key_code": hold_key,
                "modifiers": {"optional": ["any"]},
            },
            "to_if_held_down": [
                {
                    "set_variable": {
                        "name": self.BRACKET_LAYER_VAR,
                        "value": 1,
                    }
                },
            ],
            "to_if_alone": [
                *self.create_output_actions("a", shifted_tap, clear_shift_once),
            ],
            "to_after_key_up": [
                {
                    "set_variable": {
                        "name": self.BRACKET_LAYER_VAR,
                        "value": 0,
                    }
                },
            ],
        }
        if extra_conditions is None:
            return self.with_artsey_enabled_condition(manipulator)
        manipulator["conditions"] = extra_conditions
        return manipulator


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ARTSEY Karabiner complex modification assets.",
    )
    parser.add_argument(
        "--asset-output",
        default="artsey_complex_modifications.json",
        help="path for the complex_modifications asset output",
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="also install the generated asset into Karabiner's complex_modifications directory",
    )
    parser.add_argument(
        "--install-asset-output",
        default=str(
            Path.home() / ".config/karabiner/assets/complex_modifications/artsey_complex_modifications.json"
        ),
        help="path for the installed complex_modifications asset output (used with --install)",
    )
    args = parser.parse_args()

    generator = ArtseyLeftKarabinerGenerator()
    asset_workspace_path = generator.save_complex_modifications_asset(args.asset_output)
    print(f"Generated asset: {asset_workspace_path}")
    if args.install:
        asset_install_path = generator.save_complex_modifications_asset(
            args.install_asset_output
        )
        print(f"Installed asset: {asset_install_path}")


if __name__ == "__main__":
    main()
