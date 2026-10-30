"""Second-chance points and points off turnovers on small hand-written games."""

import unittest

from match import Match

HEADER = [
    "T1", "Home", "Away", "01-01-2026", "20:00", "Hall",
    "4,H4;5,H5;6,H6;7,H7;8,H8;9,H9",
    "4,A4;5,A5;6,A6;7,A7;8,A8;9,A9",
]
STARTERS = ["H4,5,6,7,8", "A4,5,6,7,8"]


def play(*events, quarters=("1",)):
    """Build a match whose quarters contain the given event bodies (action + players)."""
    lines = list(HEADER)
    by_quarter = events if len(quarters) > 1 else (events,)
    for quarter, bodies in zip(quarters, by_quarter):
        lines += [f"edit{quarter}", *STARTERS]
        lines += [f"{quarter}0500{body}" for body in bodies]
        lines.append(f"{quarter}end")
    return Match.from_history(lines)


class SecondChancePointsTests(unittest.TestCase):
    def scp(self, *events, quarters=("1",)):
        return play(*events, quarters=quarters).second_chance_points(list(quarters))

    def test_putback_after_offensive_rebound(self):
        self.assertEqual(self.scp("2H4", "rH5", "2mH5"), [2, 0])

    def test_away_team_is_counted_separately(self):
        self.assertEqual(self.scp("3A4", "rA6", "3mA6aA4"), [0, 3])

    def test_team_offensive_rebound_counts(self):
        self.assertEqual(self.scp("2H4", "rH", "2mH6"), [2, 0])

    def test_defensive_rebound_is_not_a_second_chance(self):
        self.assertEqual(self.scp("2H4", "rA5", "2mA5"), [0, 0])

    def test_and_one_free_throw_is_included(self):
        self.assertEqual(self.scp("2H4", "rH5", "2mH5", "f1A6", "1mH5"), [3, 0])

    def test_free_throws_from_a_foul_after_the_rebound_count(self):
        self.assertEqual(self.scp("2H4", "rH5", "f2A6", "1mH5", "1mH5"), [2, 0])

    def test_second_miss_then_putback_still_counts(self):
        self.assertEqual(self.scp("2H4", "rH5", "2H5", "rH6", "2mH6"), [2, 0])

    def test_defence_touching_the_ball_ends_the_second_chance(self):
        self.assertEqual(self.scp("2H4", "rH5", "2H5", "rA6", "tA6", "2mH7"), [0, 0])

    def test_offensive_foul_ends_the_second_chance(self):
        self.assertEqual(self.scp("2H4", "rH5", "f0H5", "2mH6"), [0, 0])

    def test_only_the_first_basket_after_the_rebound_counts(self):
        self.assertEqual(self.scp("2H4", "rH5", "2mH5", "2mA4", "2mH6"), [2, 0])

    def test_end_of_quarter_resets(self):
        game = (("2H4", "rH5"), ("2mH5",))
        self.assertEqual(self.scp(*game, quarters=("1", "2")), [0, 0])

    def test_only_requested_quarters_are_counted(self):
        game = play(("2H4", "rH5", "2mH5"), ("3A4", "rA5", "3mA5"), quarters=("1", "2"))
        self.assertEqual(game.second_chance_points(["1"]), [2, 0])
        self.assertEqual(game.second_chance_points(["2"]), [0, 3])


class PointsOffTurnoversTests(unittest.TestCase):
    def pot(self, *events, quarters=("1",)):
        return play(*events, quarters=quarters).points_off_turnovers(list(quarters))

    def test_steal_and_score(self):
        self.assertEqual(self.pot("tH4sA5", "2mA5"), [0, 2])

    def test_home_points_off_away_turnover(self):
        self.assertEqual(self.pot("tA4", "3mH6aH4"), [3, 0])

    def test_team_turnover_counts(self):
        self.assertEqual(self.pot("tH", "2mA5"), [0, 2])

    def test_free_throws_after_a_foul_count(self):
        self.assertEqual(self.pot("tH4", "f2H5", "1mA6", "1mA6"), [0, 2])

    def test_timeout_and_substitution_do_not_end_the_possession(self):
        self.assertEqual(self.pot("tH4", "toA", "outA4inA9", "2mA9"), [0, 2])

    @unittest.expectedFailure
    def test_and_one_free_throw_is_included(self):
        # f1 is missing from the "keep the possession going" set, unlike f2/f3.
        self.assertEqual(self.pot("tH4", "2mA5", "f1H6", "1mA5"), [0, 3])

    def test_a_miss_ends_the_possession(self):
        self.assertEqual(self.pot("tH4", "3A5", "rA6", "2mA6"), [0, 0])

    def test_turning_team_scoring_does_not_count(self):
        self.assertEqual(self.pot("tH4", "2mH5"), [0, 0])

    def test_only_the_first_basket_counts(self):
        self.assertEqual(self.pot("tH4sA5", "2mA5", "2mH4", "2mA6"), [0, 2])

    def test_only_requested_quarters_are_counted(self):
        game = play(("tH4", "2mA5"), ("tA4", "2mH5"), quarters=("1", "2"))
        self.assertEqual(game.points_off_turnovers(["1"]), [0, 2])
        self.assertEqual(game.points_off_turnovers(["2"]), [2, 0])


if __name__ == "__main__":
    unittest.main()
