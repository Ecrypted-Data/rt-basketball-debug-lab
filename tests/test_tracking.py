import unittest

from basketball.detection import Ball
from basketball.tracking import Tracker


class TrackerTest(unittest.TestCase):
    def test_visible_detection_is_reported(self) -> None:
        result = Tracker().update(0, 30.0, Ball(10, 20, 5))

        self.assertEqual(result.ball, Ball(10, 20, 5))
        self.assertEqual(result.status, "visible")

    def test_missing_detection_is_lost_not_last_position(self) -> None:
        tracker = Tracker()
        tracker.update(0, 30.0, Ball(10, 20, 5))

        result = tracker.update(1, 30.0, None)

        self.assertIsNone(result.ball)
        self.assertEqual(result.status, "lost")

    def test_lost_frame_does_not_poison_next_detection(self) -> None:
        tracker = Tracker()
        tracker.update(0, 30.0, Ball(10, 20, 5))
        tracker.update(1, 30.0, None)

        result = tracker.update(2, 30.0, Ball(30, 40, 6))

        self.assertEqual(result.ball, Ball(30, 40, 6))
        self.assertEqual(result.status, "visible")


if __name__ == "__main__":
    unittest.main()
