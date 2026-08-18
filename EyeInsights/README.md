# 👁 Eye Insights
### AI Based Exam Fraud Detection Using Eye Movement Analysis

Eye Insights is a desktop exam-proctoring assistant that watches a
student through the webcam during an online/offline exam, tracks eye
movement, blinking and head pose using MediaPipe FaceMesh, and raises
warnings — with a live fraud score — whenever suspicious behaviour is
detected. At the end of the exam it produces a full PDF report.

---

## 1. Features

- **Modern GUI** built with CustomTkinter (blue/white professional theme)
- **Live webcam monitoring** with an on-frame status banner
- **468-point face mesh** via MediaPipe, including iris landmarks
- **Eye gaze direction** (Center / Left / Right / Up / Down)
- **Blink detection** using the Eye Aspect Ratio (EAR) method
- **Head pose estimation** (yaw/pitch) via OpenCV `solvePnP`
- **Fraud scoring engine** with cooldown + minimum-duration logic to
  avoid false positives from single noisy frames
- **No-face / multiple-faces detection**
- **Automatic screenshots** on every warning
- **SQLite database** for students, exam logs, warnings and summaries
- **PDF report generation** (ReportLab) with embedded screenshots
- **Report screen** with a matplotlib warning-breakdown chart

---

## 2. Project Structure

```
EyeInsights/
├── main.py                 # Application entry point
├── config.py                # Central configuration (colors, thresholds, paths)
├── requirements.txt
├── README.md
├── .gitignore
│
├── assets/                  # icons / images / sounds
├── ui/                       # CustomTkinter screens & widgets
│   ├── login.py
│   ├── dashboard.py
│   ├── exam.py               # ExamController (business logic glue)
│   ├── report.py
│   ├── warning.py
│   ├── widgets.py
│   └── styles.py
│
├── ai/                        # Computer-vision / AI pipeline
│   ├── camera.py
│   ├── face_detector.py
│   ├── eye_tracker.py
│   ├── blink_detector.py
│   ├── head_pose.py
│   ├── fraud_engine.py
│   └── monitoring.py
│
├── database/
│   ├── database.py
│   └── models.py
│
├── utils/
│   ├── helper.py
│   ├── logger.py
│   ├── timer.py
│   ├── screenshot.py
│   └── pdf_generator.py
│
├── models/                   # (reserved for cached ML model files)
├── reports/                   # Generated PDF reports
├── screenshots/                # Auto-captured evidence screenshots
├── logs/                        # Rotating application log files
└── tests/                        # Unit tests (no camera required)
```

---

## 3. Application Flow

```
main.py → Login Screen → Dashboard → Start Monitoring → Open Camera
   → Detect Face → Track Eyes → Blink Detection → Head Pose Detection
   → Fraud Engine → Store Logs → Capture Screenshot → Generate Report
   → End Exam
```

---

## 4. Installation

### 4.1 Prerequisites
- Python 3.11 (recommended)
- A working webcam
- Windows / macOS / Linux with a display (this is a desktop GUI app)

### 4.2 Create and activate a virtual environment

**Windows (PowerShell):**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4.3 Install dependencies
```bash
pip install -r requirements.txt
```

### 4.4 Run the project
```bash
python main.py
```

On first launch, `config.py` automatically creates the `reports/`,
`screenshots/`, `logs/` and `models/` folders and a fresh
`eye_insights.db` SQLite database if they don't already exist.

---

## 5. Using the App

1. **Login Screen** — enter the student's name, register number,
   department and subject, then click **Start Exam**.
2. **Dashboard** — click **Start Monitoring** to open the webcam and
   begin the AI pipeline. Live status cards show blink count, eye
   direction, head position, warning count, fraud score and the
   exam timer.
3. Every time a violation is sustained for long enough (to filter out
   noise) a **warning toast** appears, a screenshot is captured, and
   the event is written to the database.
4. If warnings exceed the configured maximum
   (`MAX_WARNINGS_ALLOWED` in `config.py`), the exam is automatically
   flagged and ended.
5. Click **Stop Monitoring** to end the exam manually — a PDF report
   is generated immediately.
6. Click **View Report** to see the summary, a warning-breakdown
   chart, and to open/download the PDF.

---

## 6. Configuration

All tunable behaviour lives in `config.py`:

| Setting | Purpose |
|---|---|
| `EAR_BLINK_THRESHOLD` | EAR value below which eyes are considered closed |
| `GAZE_LEFT_THRESHOLD` / `GAZE_RIGHT_THRESHOLD` | Horizontal iris-ratio thresholds |
| `HEAD_YAW_LEFT_THRESHOLD` / `HEAD_YAW_RIGHT_THRESHOLD` | Head yaw angle thresholds (degrees) |
| `FRAUD_POINTS_*` | Points added to the fraud score per violation type |
| `MAX_WARNINGS_ALLOWED` | Warning count that auto-flags the exam |
| `FRAUD_SCORE_FAIL_THRESHOLD` | Fraud score that marks the result as "Fail" |
| `DEFAULT_EXAM_DURATION_MINUTES` | Exam timer length |

---

## 7. Architecture Notes

- **`ai/monitoring.py`** is the orchestration layer: it pulls a frame
  from `ai/camera.py`, runs `ai/face_detector.py`
  (MediaPipe FaceMesh), then `ai/eye_tracker.py`,
  `ai/blink_detector.py` and `ai/head_pose.py` on the resulting
  landmarks, and finally feeds everything into
  `ai/fraud_engine.py` to get a fraud score and, optionally, a new
  `WarningEvent`.
- **`ui/exam.py`** (`ExamController`) is the glue between the AI
  pipeline and persistence: it owns a `MonitoringSession`, an
  `ExamTimer`, and talks to `database/database.py` to store logs,
  warnings and the final summary, then calls
  `utils/pdf_generator.py` to build the PDF.
- **`ui/dashboard.py`** is purely presentational: it polls
  `ExamController.poll()` on a `Tkinter.after()` loop, renders the
  frame and updates the status cards.
- The fraud engine uses a **minimum sustained duration** +
  **per-warning-type cooldown** so a single flickering frame doesn't
  spam warnings, while genuine repeated behaviour still accumulates
  score over time.

---

## 8. Running Tests

Unit tests cover the logic that doesn't require a camera or display
(helpers, timer, fraud engine, database):

```bash
python -m unittest discover tests
```

---

## 9. Disclaimer

This project is built for **academic / final-year engineering
demonstration purposes**. It illustrates AI-based behavioural signals
that *may* correlate with exam malpractice (looking away, head
turning, face absence). It is **not** a certified proctoring product
and should not be the sole basis for any disciplinary decision in a
real examination without human review of the generated evidence.
