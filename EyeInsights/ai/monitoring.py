"""
ai/monitoring.py
-----------------
Top level orchestrator that ties Camera -> FaceDetector -> EyeTracker
-> BlinkDetector -> HeadPoseEstimator -> FraudEngine together into a
single `process_next_frame()` call used by the dashboard's polling loop.
"""

import cv2

from ai.blink_detector import BlinkDetector
from ai.camera import Camera
from ai.face_detector import FaceDetector
from ai.eye_tracker import EyeTracker
from ai.fraud_engine import FraudEngine
from ai.head_pose import HeadPoseEstimator
from config import COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING
from utils.logger import get_logger

logger = get_logger("Monitoring")

_ALL_CONDITION_TYPES = [
    "FACE_MISSING", "MULTIPLE_FACES", "LOOK_LEFT", "LOOK_RIGHT",
    "LOOK_DOWN", "HEAD_TURNED", "EYES_CLOSED_LONG",
]


class MonitoringResult:
    """Everything the UI needs to render for a single processed frame."""

    def __init__(self, frame_rgb, analysis, face_found: bool):
        self.frame_rgb = frame_rgb
        self.analysis = analysis
        self.face_found = face_found


class MonitoringSession:
    """Owns the camera and the whole AI pipeline for one exam session."""

    def __init__(self):
        self.camera = Camera()
        self.face_detector = FaceDetector()
        self.eye_tracker = EyeTracker()
        self.blink_detector = BlinkDetector()
        self.head_pose_estimator = HeadPoseEstimator()
        self.fraud_engine = FraudEngine()
        self._active = False

    def start(self) -> bool:
        """Open the camera and reset all AI state. Returns True on success."""
        opened = self.camera.open()
        if not opened:
            logger.error("MonitoringSession failed to start: camera not available.")
            return False
        self.blink_detector.reset()
        self.fraud_engine.reset()
        self._active = True
        logger.info("MonitoringSession started.")
        return True

    def stop(self):
        """Release the camera and mark the session inactive."""
        self.camera.release()
        self._active = False
        logger.info("MonitoringSession stopped.")

    @property
    def is_active(self) -> bool:
        return self._active

    def process_next_frame(self):
        """
        Grab one frame from the camera, run the full AI pipeline, and
        return a MonitoringResult (or None if no frame was available).
        """
        if not self._active:
            return None

        frame_bgr = self.camera.read_frame_bgr()
        if frame_bgr is None:
            return None

        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        detection = self.face_detector.process(frame_rgb)

        if detection.no_face:
            self._clear_face_conditions()
            analysis = self.fraud_engine.evaluate(
                face_count=0, gaze_direction="CENTER", head_direction="NORMAL",
                ear=0.0, eyes_closed=False, eyes_closed_duration=0.0,
                blink_count=self.blink_detector._blink_count,
            )
            self._draw_status_banner(frame_bgr, analysis)
            return MonitoringResult(
                frame_rgb=cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB),
                analysis=analysis, face_found=False,
            )

        if detection.multiple_faces:
            analysis = self.fraud_engine.evaluate(
                face_count=detection.face_count, gaze_direction="CENTER",
                head_direction="NORMAL", ear=0.0, eyes_closed=False,
                eyes_closed_duration=0.0, blink_count=self.blink_detector._blink_count,
            )
            self._draw_status_banner(frame_bgr, analysis)
            self._draw_face_boxes(frame_bgr, detection)
            return MonitoringResult(
                frame_rgb=cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB),
                analysis=analysis, face_found=True,
            )

        landmarks = detection.primary_landmarks

        gaze_result = self.eye_tracker.estimate_gaze(landmarks)
        blink_result = self.blink_detector.process(landmarks)
        head_result = self.head_pose_estimator.estimate(
            landmarks, detection.image_width, detection.image_height
        )

        self._clear_inactive_conditions(gaze_result.direction, head_result.direction,
                                         blink_result.eyes_closed)

        analysis = self.fraud_engine.evaluate(
            face_count=1,
            gaze_direction=gaze_result.direction,
            head_direction=head_result.direction,
            ear=blink_result.ear,
            eyes_closed=blink_result.eyes_closed,
            eyes_closed_duration=blink_result.eyes_closed_duration,
            blink_count=blink_result.blink_count,
        )

        self._draw_landmarks(frame_bgr, landmarks, gaze_result)
        self._draw_status_banner(frame_bgr, analysis)

        return MonitoringResult(
            frame_rgb=cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB),
            analysis=analysis, face_found=True,
        )

    def get_raw_frame_bgr(self):
        """Expose the last raw BGR frame's re-read for screenshot purposes."""
        return self.camera.read_frame_bgr()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _clear_face_conditions(self):
        for cond in ("LOOK_LEFT", "LOOK_RIGHT", "LOOK_DOWN", "HEAD_TURNED",
                     "EYES_CLOSED_LONG", "MULTIPLE_FACES"):
            self.fraud_engine.clear_condition(cond)

    def _clear_inactive_conditions(self, gaze_direction, head_direction, eyes_closed):
        self.fraud_engine.clear_condition("FACE_MISSING")
        self.fraud_engine.clear_condition("MULTIPLE_FACES")

        if gaze_direction != "LEFT":
            self.fraud_engine.clear_condition("LOOK_LEFT")
        if gaze_direction != "RIGHT":
            self.fraud_engine.clear_condition("LOOK_RIGHT")
        if gaze_direction != "DOWN":
            self.fraud_engine.clear_condition("LOOK_DOWN")
        if head_direction == "NORMAL":
            self.fraud_engine.clear_condition("HEAD_TURNED")
        if not eyes_closed:
            self.fraud_engine.clear_condition("EYES_CLOSED_LONG")

    @staticmethod
    def _draw_landmarks(frame_bgr, landmarks, gaze_result):
        for point in (gaze_result.left_eye_center, gaze_result.right_eye_center):
            cv2.circle(frame_bgr, (int(point[0]), int(point[1])), 3, (0, 255, 0), -1)

    @staticmethod
    def _draw_face_boxes(frame_bgr, detection):
        for face_landmarks in detection.landmarks_list:
            xs = [p[0] for p in face_landmarks]
            ys = [p[1] for p in face_landmarks]
            cv2.rectangle(
                frame_bgr,
                (int(min(xs)), int(min(ys))),
                (int(max(xs)), int(max(ys))),
                (0, 0, 255), 2,
            )

    @staticmethod
    def _draw_status_banner(frame_bgr, analysis):
        color_map = {"OK": (46, 125, 50), "CAUTION": (249, 168, 37), "DANGER": (198, 40, 40)}
        color_bgr = color_map.get(analysis.status_level, (46, 125, 50))
        # OpenCV uses BGR; the map above stores (R, G, B)-ish reversed for clarity.
        color_bgr = (color_bgr[2], color_bgr[1], color_bgr[0])

        height, width = frame_bgr.shape[:2]
        cv2.rectangle(frame_bgr, (0, height - 34), (width, height), color_bgr, -1)
        cv2.putText(
            frame_bgr, analysis.status_text, (10, height - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA,
        )

    def close(self):
        """Fully release resources (camera + MediaPipe graph)."""
        self.stop()
        self.face_detector.close()
