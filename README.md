HEAD
# web_3
=======
Variant 18 — Periodic Image Transform (FastAPI)

This small FastAPI app implements lab variant 18: it multiplies an uploaded image by a periodic function (sin or cos) along either the vertical or horizontal axis with a user-specified period. The app returns the processed image and color histograms for original and processed images.

Files added:
- `app.py` — FastAPI application and routes
- `image_ops.py` — image processing utilities (apply_periodic, save_histogram)
- `templates/index.html` — upload form
- `templates/result.html` — result page
- `static/styles.css` — minimal styling
- `requirements.txt` — Python dependencies
- `tests/test_image_ops.py` — unit test for processing function

How to run locally (recommended inside a virtualenv):

1) Create and activate a virtual environment (Windows PowerShell example):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

2) Start the app with uvicorn:

```powershell
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

3) Open http://127.0.0.1:8000 in your browser, upload an image and set parameters.

Run tests:

```powershell
python -m pytest -q
```

Notes and assumptions:
- The periodic multiplier is normalized to [0,1] using 0.5*(1+sin/cos(...)), so no negative values.
- The UI is minimal and intended as a functional prototype for the lab assignment.
- If you plan to deploy, consider cleaning up old files in `static/` and adding limits on upload size.

Next steps (suggestions):
- Add input validation and size limits.
- Add option to use both axes (variant 19 style) or change amplitude/offset.
- Add better styling and sample images in `static/`.

