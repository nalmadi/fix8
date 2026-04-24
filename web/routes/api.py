"""Fix8 Web REST API — full desktop-feature parity."""
import os
import io
import json
import time
import uuid
import csv
from collections import OrderedDict

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")  # MUST be before pyplot
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpatches

from flask import Blueprint, send_file, jsonify, request, session, abort
from werkzeug.utils import secure_filename
from PIL import Image

from src.core import Fix8Core, ALGORITHM_REGISTRY


api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------- Session storage with expiry + LRU cap ----------------

ACTIVE_SESSIONS: "OrderedDict[str, dict]" = OrderedDict()
SESSION_TTL_SECONDS = 60 * 60  # 1 hour of inactivity
MAX_SESSIONS = 200


def _purge_sessions():
    now = time.time()
    expired = [k for k, v in ACTIVE_SESSIONS.items() if now - v["last_access"] > SESSION_TTL_SECONDS]
    for k in expired:
        ACTIVE_SESSIONS.pop(k, None)
    while len(ACTIVE_SESSIONS) > MAX_SESSIONS:
        ACTIVE_SESSIONS.popitem(last=False)


def get_engine() -> Fix8Core:
    """Retrieve or create the Fix8Core engine for the current client session."""
    _purge_sessions()
    if "uid" not in session:
        session["uid"] = str(uuid.uuid4())
    uid = session["uid"]
    if uid not in ACTIVE_SESSIONS:
        ACTIVE_SESSIONS[uid] = {"engine": Fix8Core(), "last_access": time.time()}
    ACTIVE_SESSIONS.move_to_end(uid)
    ACTIVE_SESSIONS[uid]["last_access"] = time.time()
    return ACTIVE_SESSIONS[uid]["engine"]


# ---------------- Helpers ----------------

def _require_data(engine):
    if engine.eye_events is None or engine.eye_events.empty:
        abort(400, description="No trial loaded")


def _fixations_df(engine):
    return engine.eye_events[engine.eye_events["eye_event"] == "fixation"]


def _state_payload(engine):
    payload = {
        "has_data": engine.eye_events is not None and not engine.eye_events.empty,
        "current_fixation": engine.current_fixation,
        "selected_fixation": engine.selected_fixation,
        "algorithm": engine.algorithm,
        "has_suggestions": engine.suggested_corrections is not None,
        "has_aoi": engine.aoi is not None and not engine.aoi.empty,
        "has_image": bool(engine.image_file_path),
        "image_url": getattr(engine, "image_url", None),
        "fixations": [],
        "aois": [],
        "suggestions": [],
        "stats": engine.trial_stats() if engine.eye_events is not None else {},
        "can_undo": not engine.state_history.is_empty(),
    }
    if payload["has_data"]:
        fix_df = _fixations_df(engine)
        payload["fixations"] = fix_df[["x_cord", "y_cord", "duration"]].to_dict(orient="records")
    if payload["has_aoi"]:
        payload["aois"] = engine.aoi[["kind", "name", "x", "y", "width", "height"]].to_dict(orient="records")
    if payload["has_suggestions"]:
        sug = engine.suggested_corrections
        payload["suggestions"] = [{"x": float(r[0]), "y": float(r[1])} for r in sug]
    return payload


def _ok(engine, message="ok", extra=None):
    body = {"message": message, "state": _state_payload(engine)}
    if extra:
        body.update(extra)
    return jsonify(body)


def _load_json_trial(engine, path):
    with open(path, "r", encoding="utf-8") as f:
        trial = json.load(f)
    x_cord, y_cord, duration, ts = [], [], [], []
    if isinstance(trial, dict) and "fixations" in trial:
        for fx in trial["fixations"]:
            x_cord.append(float(fx[0]))
            y_cord.append(float(fx[1]))
            duration.append(float(fx[2]))
        if "time_stamps" in trial:
            ts = [float(t) for t in trial["time_stamps"]]
    elif isinstance(trial, dict):
        for key in trial:
            x_cord.append(float(trial[key][0]))
            y_cord.append(float(trial[key][1]))
            duration.append(float(trial[key][2]))
    else:
        for fx in trial:
            x_cord.append(float(fx[0]))
            y_cord.append(float(fx[1]))
            duration.append(float(fx[2]))
    df = pd.DataFrame({"x_cord": x_cord, "y_cord": y_cord, "duration": duration, "eye_event": "fixation"})
    if ts and len(ts) == len(df):
        df["time_stamp"] = ts
    engine.eye_events = df
    engine.trial_path = path
    engine.current_fixation = -1
    engine.suggested_corrections = None
    engine.state_history = engine.state_history.__class__()  # reset history


# ---------------- State / navigation ----------------

@api_bp.route("/state", methods=["GET"])
def api_state():
    return jsonify(_state_payload(get_engine()))


@api_bp.route("/reset", methods=["POST"])
def api_reset():
    """Wipe the current session's engine."""
    uid = session.get("uid")
    if uid:
        ACTIVE_SESSIONS.pop(uid, None)
    return _ok(get_engine(), "reset")


@api_bp.route("/load_demo", methods=["POST"])
def api_load_demo():
    engine = get_engine()
    demo_path = os.path.join(os.path.dirname(__file__), "..", "static", "demo_data", "demo_trial.json")
    if not os.path.exists(demo_path):
        return jsonify({"error": f"Demo file not found at {demo_path}"}), 404
    _load_json_trial(engine, demo_path)
    engine.image_file_path = os.path.join(os.path.dirname(__file__), "..", "static", "demo_data", "demo_image.png")
    engine.image_url = "/demo_data/demo_image.png"
    return _ok(engine, "demo loaded", {"fixation_count": len(engine.eye_events)})


@api_bp.route("/action/move", methods=["POST"])
def api_move():
    direction = (request.json or {}).get("direction", "")
    engine = get_engine()
    if direction in ("right", "next"):
        engine.next_fixation()
    elif direction in ("left", "previous"):
        engine.previous_fixation()
    else:
        return jsonify({"error": "direction must be left|right|next|previous"}), 400
    return _ok(engine, f"moved {direction}")


@api_bp.route("/action/update_fixation", methods=["POST"])
def api_update_fixation():
    data = request.json or {}
    try:
        index = int(data["index"])
        x = float(data["x"])
        y = float(data["y"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "body requires index (int), x (float), y (float)"}), 400
    engine = get_engine()
    _require_data(engine)
    engine.update_fixation(index, x, y)
    return _ok(engine, f"updated fixation {index}")


@api_bp.route("/action/delete_fixation", methods=["POST"])
def api_delete_fixation():
    data = request.json or {}
    try:
        index = int(data["index"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "body requires index (int)"}), 400
    engine = get_engine()
    _require_data(engine)
    engine.delete_fixation(index)
    return _ok(engine, f"deleted fixation {index}")


@api_bp.route("/action/assign_line", methods=["POST"])
def api_assign_line():
    data = request.json or {}
    try:
        index = int(data.get("index", get_engine().current_fixation))
    except (TypeError, ValueError):
        return jsonify({"error": "index must be int"}), 400
    engine = get_engine()
    _require_data(engine)
    mode = data.get("mode", "number")
    if mode == "above":
        engine.assign_above(index)
    elif mode == "below":
        engine.assign_below(index)
    elif mode == "number":
        try:
            line = int(data["line"])
        except (KeyError, TypeError, ValueError):
            return jsonify({"error": "line (int) required for mode=number"}), 400
        engine.assign_to_line(index, line)
    else:
        return jsonify({"error": "mode must be above|below|number"}), 400
    return _ok(engine, f"assigned line ({mode})")


@api_bp.route("/action/accept_suggestion", methods=["POST"])
def api_accept_suggestion():
    engine = get_engine()
    _require_data(engine)
    if engine.suggested_corrections is None:
        return jsonify({"error": "no suggestions active; run an algorithm in assisted mode first"}), 400
    engine.accept_current_suggestion()
    return _ok(engine, "suggestion accepted")


@api_bp.route("/action/accept_all_suggestions", methods=["POST"])
def api_accept_all():
    engine = get_engine()
    _require_data(engine)
    if engine.suggested_corrections is None:
        return jsonify({"error": "no suggestions active"}), 400
    engine.accept_all_suggestions()
    return _ok(engine, "all suggestions accepted")


@api_bp.route("/action/undo", methods=["POST"])
def api_undo():
    engine = get_engine()
    ok = engine.undo()
    if not ok:
        return jsonify({"error": "nothing to undo"}), 400
    return _ok(engine, "undone")


# ---------------- AOI detection ----------------

@api_bp.route("/aoi/detect", methods=["POST"])
def api_detect_aoi():
    engine = get_engine()
    if not engine.image_file_path:
        return jsonify({"error": "no stimulus image loaded"}), 400
    data = request.json or {}
    level = data.get("level", "sub-line")
    if level not in ("line", "sub-line"):
        return jsonify({"error": "level must be line|sub-line"}), 400
    try:
        engine.aoi_width = int(data.get("aoi_width", engine.aoi_width))
        engine.aoi_height = int(data.get("aoi_height", engine.aoi_height))
    except (TypeError, ValueError):
        return jsonify({"error": "aoi_width and aoi_height must be ints"}), 400
    engine.detect_aois(level=level)
    return _ok(engine, "aois detected", {"aoi_count": len(engine.aoi)})


# ---------------- Correction algorithms ----------------

@api_bp.route("/algorithm/list", methods=["GET"])
def api_algorithm_list():
    return jsonify({"algorithms": list(ALGORITHM_REGISTRY.keys())})


@api_bp.route("/algorithm/run", methods=["POST"])
def api_algorithm_run():
    data = request.json or {}
    name = data.get("name")
    mode = data.get("mode", "auto")
    if mode not in ("auto", "assisted"):
        return jsonify({"error": "mode must be auto|assisted"}), 400
    if name not in ALGORITHM_REGISTRY:
        return jsonify({"error": f"unknown algorithm; valid: {list(ALGORITHM_REGISTRY)}"}), 400
    engine = get_engine()
    _require_data(engine)
    if not engine.image_file_path:
        return jsonify({"error": "no stimulus image loaded — upload an image first"}), 400
    try:
        engine.run_algorithm(name, mode=mode)
    except Exception as e:
        return jsonify({"error": f"algorithm failed: {e}"}), 500
    return _ok(engine, f"{name} ({mode}) completed")


# ---------------- Distortions ----------------

def _parse_threshold(default=5.0):
    data = request.json or {}
    try:
        return float(data.get("threshold", default))
    except (TypeError, ValueError):
        abort(400, description="threshold must be numeric")


@api_bp.route("/distort/noise", methods=["POST"])
def api_distort_noise():
    t = _parse_threshold(5)
    engine = get_engine()
    _require_data(engine)
    engine.apply_noise(t)
    return _ok(engine, "noise applied")


@api_bp.route("/distort/slope", methods=["POST"])
def api_distort_slope():
    t = _parse_threshold(5)
    engine = get_engine()
    _require_data(engine)
    engine.apply_slope(t)
    return _ok(engine, "slope applied")


@api_bp.route("/distort/offset", methods=["POST"])
def api_distort_offset():
    t = _parse_threshold(10)
    engine = get_engine()
    _require_data(engine)
    engine.apply_offset(t)
    return _ok(engine, "offset applied")


@api_bp.route("/distort/shift", methods=["POST"])
def api_distort_shift():
    t = _parse_threshold(5)
    engine = get_engine()
    _require_data(engine)
    if not engine.image_file_path:
        return jsonify({"error": "shift requires a stimulus image"}), 400
    engine.apply_shift(t)
    return _ok(engine, "shift applied")


# ---------------- Filters ----------------

@api_bp.route("/filter/lowpass", methods=["POST"])
def api_filter_lowpass():
    t = _parse_threshold(80)
    engine = get_engine()
    _require_data(engine)
    engine.filter_lowpass_duration(t)
    return _ok(engine, f"lowpass < {t}ms removed")


@api_bp.route("/filter/highpass", methods=["POST"])
def api_filter_highpass():
    t = _parse_threshold(800)
    engine = get_engine()
    _require_data(engine)
    engine.filter_highpass_duration(t)
    return _ok(engine, f"highpass > {t}ms removed")


@api_bp.route("/filter/outlier", methods=["POST"])
def api_filter_outlier():
    t = _parse_threshold(2.5)
    engine = get_engine()
    _require_data(engine)
    engine.filter_outlier_duration(t)
    return _ok(engine, f"outliers beyond {t} std removed")


@api_bp.route("/filter/outside_screen", methods=["POST"])
def api_filter_outside():
    engine = get_engine()
    _require_data(engine)
    if not engine.image_file_path:
        return jsonify({"error": "stimulus image required to know screen bounds"}), 400
    with Image.open(engine.image_file_path) as img:
        w, h = img.size
    engine.filter_outside_screen(w, h)
    return _ok(engine, "fixations outside screen removed")


@api_bp.route("/filter/merge", methods=["POST"])
def api_filter_merge():
    data = request.json or {}
    try:
        dur = float(data.get("duration_threshold", 50))
        disp = float(data.get("dispersion_threshold", 20))
    except (TypeError, ValueError):
        return jsonify({"error": "duration_threshold and dispersion_threshold must be numeric"}), 400
    engine = get_engine()
    _require_data(engine)
    engine.merge_short_fixations(dur, disp)
    return _ok(engine, "fixations merged")


# ---------------- Upload trial / image ----------------

def _storage_dir():
    return os.environ.get("STORAGE_PATH", os.path.join(os.path.dirname(__file__), "..", "uploads"))


@api_bp.route("/upload/trial", methods=["POST"])
def api_upload_trial():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "empty filename"}), 400
    if not f.filename.lower().endswith((".json",)):
        return jsonify({"error": "only .json accepted here"}), 400
    filename = secure_filename(f.filename)
    storage = _storage_dir()
    os.makedirs(storage, exist_ok=True)
    uid = session.get("uid", "anon")
    save_path = os.path.join(storage, f"{uid}_{uuid.uuid4().hex[:8]}_{filename}")
    f.save(save_path)
    engine = get_engine()
    try:
        _load_json_trial(engine, save_path)
    except Exception as e:
        return jsonify({"error": f"invalid trial JSON: {e}"}), 400
    return _ok(engine, "trial loaded", {"fixation_count": len(engine.eye_events)})


@api_bp.route("/upload/image", methods=["POST"])
def api_upload_image():
    if "file" not in request.files:
        return jsonify({"error": "no file"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "empty filename"}), 400
    if not f.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        return jsonify({"error": "only .png/.jpg/.jpeg accepted"}), 400
    filename = secure_filename(f.filename)
    storage = _storage_dir()
    os.makedirs(storage, exist_ok=True)
    uid = session.get("uid", "anon")
    unique = f"{uid}_{uuid.uuid4().hex[:8]}_{filename}"
    save_path = os.path.join(storage, unique)
    f.save(save_path)
    engine = get_engine()
    engine.image_file_path = save_path
    engine.image_url = f"/api/image/{unique}"
    engine.aoi = None  # force re-detection
    return _ok(engine, "image uploaded")


@api_bp.route("/image/<path:filename>", methods=["GET"])
def api_serve_image(filename):
    filename = secure_filename(filename)
    path = os.path.join(_storage_dir(), filename)
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404
    return send_file(path)


# ---------------- Export ----------------

@api_bp.route("/export/json", methods=["GET"])
def api_export_json():
    engine = get_engine()
    _require_data(engine)
    fix = _fixations_df(engine)
    payload = {
        "fixations": fix[["x_cord", "y_cord", "duration"]].values.tolist(),
    }
    if "time_stamp" in fix.columns:
        payload["time_stamps"] = fix["time_stamp"].tolist()
    buf = io.BytesIO(json.dumps(payload, indent=2).encode("utf-8"))
    return send_file(buf, mimetype="application/json", as_attachment=True, download_name="fix8_corrected.json")


@api_bp.route("/export/csv", methods=["GET"])
def api_export_csv():
    engine = get_engine()
    _require_data(engine)
    buf = io.StringIO()
    engine.eye_events.to_csv(buf, index=False)
    out = io.BytesIO(buf.getvalue().encode("utf-8"))
    return send_file(out, mimetype="text/csv", as_attachment=True, download_name="fix8_corrected.csv")


@api_bp.route("/export/aoi", methods=["GET"])
def api_export_aoi():
    engine = get_engine()
    if engine.aoi is None or engine.aoi.empty:
        return jsonify({"error": "no AOIs detected"}), 400
    buf = io.StringIO()
    engine.aoi.to_csv(buf, index=False)
    out = io.BytesIO(buf.getvalue().encode("utf-8"))
    return send_file(out, mimetype="text/csv", as_attachment=True, download_name="fix8_aoi.csv")


# ---------------- Rendering ----------------

def _truthy(q):
    return str(q).lower() in ("1", "true", "yes", "on")


@api_bp.route("/render", methods=["GET"])
def api_render():
    engine = get_engine()
    q = request.args
    show_aois = _truthy(q.get("show_aois", "0"))
    show_suggestions = _truthy(q.get("show_suggestions", "1"))
    show_saccades = _truthy(q.get("show_saccades", "1"))
    show_numbers = _truthy(q.get("show_numbers", "0"))

    fig_width, fig_height = 10, 8
    img = None
    if engine.image_file_path and os.path.exists(engine.image_file_path):
        try:
            img = np.asarray(Image.open(engine.image_file_path).convert("RGB"))
            fig_width = img.shape[1] / 100.0
            fig_height = img.shape[0] / 100.0
        except Exception:
            img = None

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=100)
    if img is not None:
        ax.imshow(img)

    if show_aois and engine.aoi is not None and not engine.aoi.empty:
        for _, row in engine.aoi.iterrows():
            rect = mpatches.Rectangle(
                (row["x"], row["y"]), row["width"], row["height"],
                linewidth=1, edgecolor=(0.5, 0.8, 0.3, 0.7), facecolor="none",
            )
            ax.add_patch(rect)

    if engine.eye_events is not None and not engine.eye_events.empty:
        fix = _fixations_df(engine)
        if not fix.empty:
            xs = fix["x_cord"].values
            ys = fix["y_cord"].values
            durs = fix["duration"].values
            sizes = [max(min(d / 10.0, 350), 30) for d in durs]

            if show_saccades:
                ax.plot(xs, ys, color=(0.22, 0.74, 0.97, 0.5), linewidth=2, zorder=1)

            ax.scatter(
                xs, ys, s=sizes,
                color=(0.94, 0.27, 0.27, 0.65),
                edgecolors=(0.86, 0.15, 0.15, 0.9),
                zorder=2,
            )

            if show_numbers:
                for i, (x, y) in enumerate(zip(xs, ys)):
                    ax.text(x + 4, y - 4, str(i + 1), fontsize=7, color="white", zorder=4)

            cur = engine.current_fixation
            if 0 <= cur < len(xs):
                ax.scatter([xs[cur]], [ys[cur]], s=sizes[cur] * 1.6, color="orange", zorder=3)

            if show_suggestions and engine.suggested_corrections is not None:
                sug = engine.suggested_corrections
                sx = sug[:, 0]
                sy = sug[:, 1]
                ax.scatter(sx, sy, s=[sz * 0.8 for sz in sizes],
                           color=(0.22, 0.56, 0.94, 0.55),
                           edgecolors=(0.15, 0.35, 0.86, 0.9),
                           zorder=2.5)

    ax.axis("off")
    plt.tight_layout(pad=0)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", transparent=True, pad_inches=0)
    buf.seek(0)
    plt.close(fig)
    return send_file(buf, mimetype="image/png")
