"""1.6 month-over-month noise floor, sized per client from prompts x engines."""
from __future__ import annotations

import fill_1_6_tracker as F


def test_reproduces_recipe_figure_at_75_observations():
    assert F.noise_points(25, 3) == 12


def test_fewer_prompts_widen_the_floor():
    assert F.noise_points(19, 2) > F.noise_points(44, 2) > 0


def test_two_engines_wider_than_three():
    assert F.noise_points(25, 2) > F.noise_points(25, 3)


def test_zero_prompts_does_not_divide_by_zero():
    assert F.noise_points(0, 0) == 98
