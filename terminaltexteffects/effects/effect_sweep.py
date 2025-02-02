"""Sweep across the canvas to reveal uncolored text, reverse sweep to color the text.

Classes:


"""

from __future__ import annotations

import random
import typing
from dataclasses import dataclass

import terminaltexteffects as tte
from terminaltexteffects.engine.base_effect import BaseEffect, BaseEffectIterator
from terminaltexteffects.utils import argvalidators
from terminaltexteffects.utils.argsdataclass import ArgField, ArgsDataClass, argclass


def get_effect_and_args() -> tuple[type[typing.Any], type[ArgsDataClass]]:
    """Return the effect class and the effect configuration dataclass.

    Returns:
        tuple[type[typing.Any], type[ArgsDataClass]]: The effect class and the effect configuration dataclass.

    """
    return Sweep, SweepConfig


@argclass(
    name="sweep",
    help="Sweep across the canvas to reveal uncolored text, reverse sweep to color the text.",
    description="sweep | Sweep across the canvas to reveal uncolored text, reverse sweep to color the text.",
    epilog=f"""{argvalidators.EASING_EPILOG}
    """,
)
@dataclass
class SweepConfig(ArgsDataClass):
    """Sweep effect configuration dataclass."""

    sweep_symbols: tuple[str, ...] = ArgField(
        cmd_name="--sweep-symbols",
        type_parser=argvalidators.Symbol.type_parser,
        nargs="+",
        default=("█", "▓", "▒", "░"),
        metavar=argvalidators.Symbol.METAVAR,
        help="Space separated list of symbols to use for the sweep shimmer.",
    )  # type: ignore[assignment]
    "tuple[str, ...] | str : Tuple of symbols to use for the sweep shimmer."

    final_gradient_stops: tuple[tte.Color, ...] = ArgField(
        cmd_name=["--final-gradient-stops"],
        type_parser=argvalidators.ColorArg.type_parser,
        nargs="+",
        default=(tte.Color("8A008A"), tte.Color("00D1FF"), tte.Color("ffffff")),
        metavar=argvalidators.ColorArg.METAVAR,
        help="Space separated, unquoted, list of colors for the character gradient (applied from bottom to top). "
        "If only one color is provided, the characters will be displayed in that color.",
    )  # type: ignore[assignment]
    "tuple[Color, ...]: Space separated, unquoted, list of colors for the character gradient "
    "(applied from bottom to top). If only one color is provided, the characters will be displayed in that color."

    final_gradient_steps: tuple[int, ...] | int = ArgField(
        cmd_name="--final-gradient-steps",
        type_parser=argvalidators.PositiveInt.type_parser,
        nargs="+",
        default=8,
        metavar=argvalidators.PositiveInt.METAVAR,
        help="Space separated, unquoted, list of the number of gradient steps to use. More steps will create a "
        "smoother and longer gradient animation.",
    )  # type: ignore[assignment]
    "tuple[int, ...] | int: Space separated, unquoted, list of the number of gradient steps to use. More steps will "
    "create a smoother and longer gradient animation."

    final_gradient_frames: int = ArgField(
        cmd_name="--final-gradient-frames",
        type_parser=argvalidators.PositiveInt.type_parser,
        default=5,
        metavar=argvalidators.PositiveInt.METAVAR,
        help="Number of frames to display each gradient step. Increase to slow down the gradient animation.",
    )  # type: ignore[assignment]
    "int: Number of frames to display each gradient step. Increase to slow down the gradient animation."

    final_gradient_direction: tte.Gradient.Direction = ArgField(
        cmd_name="--final-gradient-direction",
        type_parser=argvalidators.GradientDirection.type_parser,
        default=tte.Gradient.Direction.VERTICAL,
        metavar=argvalidators.GradientDirection.METAVAR,
        help="Direction of the final gradient.",
    )  # type: ignore[assignment]
    "Gradient.Direction : Direction of the final gradient."

    @classmethod
    def get_effect_class(cls) -> type[BaseEffect]:
        """Return the effect class associated with this configuration dataclass."""
        return Sweep


class SweepIterator(BaseEffectIterator[SweepConfig]):
    """Iterator for the sweep effect."""

    def __init__(self, effect: Sweep) -> None:
        """Initialize the effect iterator."""
        super().__init__(effect)
        self.character_final_color_map: dict[tte.EffectCharacter, tte.ColorPair] = {}
        self.pending_chars: list[tte.EffectCharacter] = []
        self.pending_groups_initial_sweep: list[list[tte.EffectCharacter]] = []
        self.pending_groups_second_sweep: list[list[tte.EffectCharacter]] = []
        self.initial_sweep_complete = False
        self.second_sweep_complete = False
        self.easer = tte.easing.eased_step_function(tte.easing.in_out_circ, 0.01)
        self.total_groups = 0
        self.groups_activated = 0
        self.build()

    def build(self) -> None:
        """Build the effect."""
        final_fg_gradient = tte.Gradient(*self.config.final_gradient_stops, steps=self.config.final_gradient_steps)
        final_gradient_mapping = final_fg_gradient.build_coordinate_color_mapping(
            self.terminal.canvas.text_bottom,
            self.terminal.canvas.text_top,
            self.terminal.canvas.text_left,
            self.terminal.canvas.text_right,
            self.config.final_gradient_direction,
        )
        shades_of_gray = [
            tte.Color("A0A0A0"),
            tte.Color("808080"),
            tte.Color("404040"),
            tte.Color("202020"),
            tte.Color("101010"),
        ]
        for character in self.terminal.get_characters(inner_fill_chars=True, outer_fill_chars=True):
            if not character.is_fill_character:
                self.character_final_color_map[character] = tte.ColorPair(
                    fg=final_gradient_mapping[character.input_coord],
                )
            initial_sweep_scn = character.animation.new_scene(scene_id="initial_sweep")
            for char in self.config.sweep_symbols:
                initial_sweep_scn.add_frame(char, 5, colors=tte.ColorPair(fg=random.choice(shades_of_gray)))
            initial_sweep_scn.add_frame(character.input_symbol, 1, colors=tte.ColorPair(fg="808080"))
            second_sweep_scn = character.animation.new_scene(scene_id="second_sweep")
            for char in self.config.sweep_symbols:
                second_sweep_scn.add_frame(
                    char,
                    5,
                    colors=tte.ColorPair(fg=random.choice(final_fg_gradient.spectrum)),
                )
            second_sweep_scn.add_frame(
                character.input_symbol,
                1,
                colors=tte.ColorPair(
                    fg=final_gradient_mapping[character.input_coord] if not character.is_fill_character else "000000",
                ),
            )

        self.pending_groups_initial_sweep = self.terminal.get_characters_grouped(
            tte.Terminal.CharacterGroup.COLUMN_RIGHT_TO_LEFT,
            inner_fill_chars=True,
            outer_fill_chars=True,
        )
        self.pending_groups_second_sweep = self.terminal.get_characters_grouped(
            tte.Terminal.CharacterGroup.COLUMN_LEFT_TO_RIGHT,
            inner_fill_chars=True,
            outer_fill_chars=True,
        )
        self.total_groups = len(self.pending_groups_initial_sweep)

    def __next__(self) -> str:
        """Return the next frame in the effect."""
        while self.pending_groups_initial_sweep or self.pending_groups_second_sweep or self.active_characters:
            _, eased_percentage = self.easer()
            if not self.initial_sweep_complete:
                while (self.groups_activated / self.total_groups) < eased_percentage:
                    if self.pending_groups_initial_sweep:
                        group = self.pending_groups_initial_sweep.pop(0)
                        for character in group:
                            self.terminal.set_character_visibility(character, is_visible=True)
                            character.animation.activate_scene(character.animation.query_scene("initial_sweep"))
                        self.active_characters.update(group)
                        self.groups_activated += 1
                if self.groups_activated == self.total_groups:
                    self.initial_sweep_complete = True
                    self.easer = tte.easing.eased_step_function(tte.easing.in_out_circ, 0.01)
                    self.groups_activated = 0
            elif not self.second_sweep_complete:
                while (self.groups_activated / self.total_groups) < eased_percentage:
                    if self.pending_groups_second_sweep:
                        group = self.pending_groups_second_sweep.pop(0)
                        for character in group:
                            character.animation.activate_scene(character.animation.query_scene("second_sweep"))
                        self.active_characters.update(group)
                        self.groups_activated += 1
                if self.groups_activated == self.total_groups:
                    self.second_sweep_complete = True

            self.update()
            return self.frame
        raise StopIteration


class Sweep(BaseEffect[SweepConfig]):
    """Effect description."""

    @property
    def _config_cls(self) -> type[SweepConfig]:
        return SweepConfig

    @property
    def _iterator_cls(self) -> type[SweepIterator]:
        return SweepIterator
