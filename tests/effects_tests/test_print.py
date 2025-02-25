import pytest

from terminaltexteffects.effects import effect_print


@pytest.mark.parametrize(
    "input_data", ["empty", "single_char", "single_column", "single_row", "medium", "tabs"], indirect=True
)
def test_print_effect(input_data, terminal_config_default_no_framerate) -> None:
    effect = effect_print.Print(input_data)
    effect.terminal_config = terminal_config_default_no_framerate
    with effect.terminal_output() as terminal:
        for frame in effect:
            terminal.print(frame)


@pytest.mark.parametrize("input_data", ["medium"], indirect=True)
def test_print_effect_terminal_color_options(input_data, terminal_config_with_color_options) -> None:
    effect = effect_print.Print(input_data)
    effect.terminal_config = terminal_config_with_color_options
    with effect.terminal_output() as terminal:
        for frame in effect:
            terminal.print(frame)


@pytest.mark.parametrize("input_data", ["medium"], indirect=True)
def test_print_final_gradient(
    terminal_config_default_no_framerate, input_data, gradient_direction, gradient_steps, gradient_stops
) -> None:
    effect = effect_print.Print(input_data)
    effect.effect_config.final_gradient_stops = gradient_stops
    effect.effect_config.final_gradient_steps = gradient_steps
    effect.effect_config.final_gradient_direction = gradient_direction
    effect.terminal_config = terminal_config_default_no_framerate
    effect.effect_config
    with effect.terminal_output() as terminal:
        for frame in effect:
            terminal.print(frame)


@pytest.mark.parametrize("print_head_return_speed", [0.1, 2])
@pytest.mark.parametrize("print_speed", [1, 5])
@pytest.mark.parametrize("input_data", ["single_char", "medium"], indirect=True)
def test_print_args(
    terminal_config_default_no_framerate, input_data, print_head_return_speed, print_speed, easing_function_1
) -> None:
    effect = effect_print.Print(input_data)
    effect.terminal_config = terminal_config_default_no_framerate
    effect.effect_config.print_head_return_speed = print_head_return_speed
    effect.effect_config.print_speed = print_speed
    effect.effect_config.print_head_easing = easing_function_1
    with effect.terminal_output() as terminal:
        for frame in effect:
            terminal.print(frame)
