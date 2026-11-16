import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import cv2

from basketball.__main__ import track_video
from basketball.detection import Ball, detect_ball
from basketball.tracking import Tracker
from basketball.video import open_video

ROOT = Path(__file__).resolve().parents[1]


class TrackingTests(unittest.TestCase):
    def test_visible_lost_and_reappeared(self):
        tracker = Tracker()
        first, second = Ball(20, 30, 10), Ball(90, 60, 15)
        results = [tracker.update(i, 20, ball) for i, ball in enumerate([first, None, None, second])]
        self.assertEqual([r.status for r in results], ['visible', 'lost', 'lost', 'visible'])
        self.assertEqual([r.ball for r in results], [first, None, None, second])
        self.assertEqual([r.time_seconds for r in results], [0, .05, .10, .15])

    def test_initial_missing_detection(self):
        result = Tracker().update(0, 20, None)
        self.assertEqual(result.status, 'lost')
        self.assertIsNone(result.ball)

    def test_all_real_video_results_match_current_detection(self):
        reader = open_video(ROOT/'samples/basketball.mp4')
        try:
            results = []
            for frame, result in track_video(reader, reader.get(cv2.CAP_PROP_FPS)):
                self.assertEqual(result.ball, detect_ball(frame), f'frame {result.frame_index}')
                results.append(result)
        finally:
            reader.release()
        self.assertEqual(len(results), 302)
        self.assertEqual(sum(r.status == 'lost' for r in results), 72)
        self.assertIsNone(results[175].ball)
        self.assertIsNotNone(results[0].ball)
        self.assertIsNotNone(results[240].ball)

    def test_cli_exports_empty_coordinates_during_loss(self):
        with tempfile.TemporaryDirectory() as tmp:
            process = subprocess.run([sys.executable, '-m', 'basketball', '--output-dir', tmp],
                                     cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            with (Path(tmp)/'tracking.csv').open() as file:
                rows = list(csv.DictReader(file))
            self.assertEqual(len(rows), 302)
            for row in rows[143:215]:
                self.assertEqual((row['status'], row['center_x'], row['center_y'], row['radius']),
                                 ('lost', '', '', ''))
            for index in (0, 215, 240, 301):
                self.assertEqual(rows[index]['status'], 'visible')
                self.assertTrue(rows[index]['center_x'])
            self.assertTrue((Path(tmp)/'annotated.mp4').is_file())


if __name__ == '__main__':
    unittest.main()
