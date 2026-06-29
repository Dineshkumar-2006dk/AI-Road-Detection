"""
YOLOv8 inference engine with OpenCV fallback simulation.

- Loads a real YOLOv8 weight file if available at MODEL_PATH.
- If the model is missing, automatically falls back to OpenCV-based
  heuristic detection so the app remains fully functional.
- All inference errors are logged with exact messages.
"""

import os
import time
import cv2
import numpy as np

_model = None
_model_error = None
_simulation_mode = False

NON_DAMAGE_CLASSES = {"normal_road", "shadow", "road_marking", "manhole", "speed_breaker"}

DAMAGE_META = {
    "pothole":            {"color": (0,   0, 255), "label": "Pothole"},
    "crack":              {"color": (0, 100, 255), "label": "Crack"},
    "longitudinal_crack": {"color": (0, 165, 255), "label": "Longitudinal Crack"},
    "transverse_crack":   {"color": (0, 215, 255), "label": "Transverse Crack"},
    "alligator_crack":    {"color": (0, 255, 255), "label": "Alligator Crack"},
    "surface_damage":     {"color": (0, 255, 100), "label": "Surface Damage"},
    "road_edge_failure":  {"color": (100,  0, 255), "label": "Road Edge Failure"},
    "road_depression":    {"color": (200,  0, 200), "label": "Road Depression"},
    "patch_failure":      {"color": (255,  0, 150), "label": "Patch Failure"},
    "water_logging":      {"color": (255, 200,  0), "label": "Water Logging"},
    "loose_gravel":       {"color": (180, 180,  0), "label": "Loose Gravel"},
}


def _get_logger():
    """Safely return Flask app logger or print fallback."""
    try:
        from flask import current_app
        return current_app.logger
    except RuntimeError:
        import logging
        return logging.getLogger(__name__)


def _get_config(key, default=None):
    try:
        from flask import current_app
        return current_app.config.get(key, default)
    except RuntimeError:
        return default


def _load_model():
    global _model, _model_error, _simulation_mode

    if _model is not None or _simulation_mode:
        return

    logger = _get_logger()
    weights = _get_config("MODEL_PATH", "")

    if not weights or not os.path.exists(weights):
        msg = (f"[YOLOv8] Weight file not found: '{weights}'. "
               "Falling back to OpenCV simulation mode.")
        logger.warning(msg)
        print(msg)
        _simulation_mode = True
        return

    try:
        from ultralytics import YOLO
        _model = YOLO(weights)
        _model_error = None
        _simulation_mode = False
        logger.info("[YOLOv8] Model loaded successfully: %s", weights)
        print(f"[YOLOv8] Model loaded: {weights}")
    except Exception as exc:
        _model_error = f"Failed to load YOLO model '{weights}': {type(exc).__name__}: {exc}"
        logger.error("[YOLOv8] %s", _model_error)
        print(f"[YOLOv8] {_model_error} — falling back to simulation.")
        _simulation_mode = True


def run_inference(image_path: str, conf_threshold: float = 0.40,
                  nms_threshold: float = 0.45) -> dict:
    _load_model()
    logger = _get_logger()
    started = time.time()

    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        msg = f"Invalid image or unreadable file: {image_path}"
        logger.error("[YOLOv8] %s", msg)
        raise ValueError(msg)

    logger.info("[Detection] Image received: %s", image_path)
    print(f"[Detection] Image received: {image_path}")

    if _simulation_mode:
        damage_detections = _opencv_simulate(img_bgr)
        sim = True
    else:
        try:
            all_detections = _yolo_detect(img_bgr, conf_threshold, nms_threshold)
        except Exception as exc:
            msg = f"Inference failed for '{image_path}': {type(exc).__name__}: {exc}"
            logger.exception("[YOLOv8] %s", msg)
            # fallback to simulation on inference error
            damage_detections = _opencv_simulate(img_bgr)
            sim = True
        else:
            damage_detections = [
                d for d in all_detections
                if d["class_name"].lower() not in NON_DAMAGE_CLASSES
            ]
            sim = False

    annotated = _draw_annotations(img_bgr.copy(), damage_detections)

    result_dir = _get_config("RESULT_FOLDER", "history")
    os.makedirs(result_dir, exist_ok=True)
    basename    = os.path.splitext(os.path.basename(image_path))[0]
    result_name = f"result_{basename}_{int(time.time())}.jpg"
    result_path = os.path.join(result_dir, result_name)

    if not cv2.imwrite(result_path, annotated):
        raise RuntimeError(f"Could not save detection image to {result_path}")

    prediction_time = time.time() - started

    from utils.severity import compute_road_condition, compute_severity

    confidences  = [d["confidence"] for d in damage_detections]
    damage_types = [d["class_name"]  for d in damage_detections]
    avg_conf     = float(np.mean(confidences)) if confidences else 0.0
    road_condition, condition_color = compute_road_condition(damage_detections, avg_conf)
    severity     = compute_severity(damage_detections, img_bgr)

    logger.info(
        "[YOLOv8] Detection completed: count=%s avg_conf=%.3f time=%.3fs sim=%s",
        len(damage_detections), avg_conf, prediction_time, sim
    )
    print(f"[YOLOv8] Detection completed: {len(damage_detections)} damage(s), "
          f"conf={avg_conf:.2f}, time={prediction_time:.3f}s, simulation={sim}")

    return {
        "result_image_path": result_path,
        "result_image_name": result_name,
        "detections":        damage_detections,
        "damage_types":      sorted(set(damage_types)),
        "confidences":       confidences,
        "road_condition":    road_condition,
        "condition_color":   condition_color,
        "severity":          severity,
        "avg_confidence":    avg_conf,          # 0.0 – 1.0
        "detection_count":   len(damage_detections),
        "prediction_time":   prediction_time,
        "simulation_mode":   sim,
        "message": ("No road damage detected." if not damage_detections
                    else f"{'Simulation: ' if sim else ''}{len(damage_detections)} damage area(s) detected."),
    }


# ── Real YOLOv8 ───────────────────────────────────────────────────────────────
def _yolo_detect(img_bgr, conf_threshold, nms_threshold):
    results = _model.predict(
        source=img_bgr,
        conf=conf_threshold,
        iou=nms_threshold,
        verbose=False,
    )
    detections = []
    for result in results:
        names = result.names if isinstance(result.names, dict) else {}
        for box in result.boxes:
            cls_id   = int(box.cls[0])
            cls_name = str(names.get(cls_id, cls_id)).lower()
            conf     = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if x2 <= x1 or y2 <= y1:
                continue
            detections.append({
                "class_name": cls_name,
                "confidence": conf,
                "bbox":       [x1, y1, x2, y2],
                "area":       (x2 - x1) * (y2 - y1),
            })
    return detections


# ── OpenCV simulation (works without any trained model) ──────────────────────
def _opencv_simulate(img_bgr: np.ndarray) -> list:
    """
    Heuristic damage detection using OpenCV morphological analysis.
    Filters out smooth or highly rectangular objects to reduce false positives.
    """
    h, w = img_bgr.shape[:2]
    gray   = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blur   = cv2.GaussianBlur(gray, (5, 5), 0)

    # 1. Adaptive + global threshold to find local dark areas (potholes)
    global_mean = cv2.mean(blur)[0]
    local_thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 51, 15
    )
    # Filter pixels that are also darker than global mean
    _, global_dark = cv2.threshold(blur, int(global_mean - 10), 255, cv2.THRESH_BINARY_INV)
    dark_mask = cv2.bitwise_and(local_thresh, global_dark)

    # Close and open mask to clean up shapes
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN,  kernel, iterations=1)

    # 2. Edges/Dilate for Cracks
    edges     = cv2.Canny(blur, 50, 150)
    crack_kern= cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    crack_mask= cv2.dilate(edges, crack_kern, iterations=2)

    detections = []
    min_area = (h * w) * 0.003   # at least 0.3% of image area

    # Find pothole/depression contours
    contours_dark, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours_dark:
        area = cv2.contourArea(cnt)
        if area < min_area:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        if bw == 0 or bh == 0:
            continue

        aspect = bw / max(bh, 1)
        rect_ratio = area / (bw * bh)
        perimeter = cv2.arcLength(cnt, True)
        circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0

        # Calculate standard dev inside the contour to measure texture/roughness
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(mask, [cnt], -1, 255, -1)
        _, std_dev = cv2.meanStdDev(gray, mask=mask)
        std_dev = float(std_dev[0][0])

        # FILTER OUT false positives:
        # A phone, book, tablet, screen or smooth card is uniform (low std_dev)
        if std_dev < 4.5:
            continue
        # A phone/book is highly rectangular (high rect_ratio) and not crack-like
        if rect_ratio > 0.85 and 0.4 < aspect < 2.5:
            continue
        # Bounding box should not be located at the top 15% of the frame (usually sky or dashboard)
        if y < h * 0.15:
            continue
        # Too low circularity means it's not a pothole/depression
        if circularity < 0.04:
            continue

        cls = "pothole" if (0.4 < aspect < 2.2 and circularity > 0.1) else "road_depression"
        conf = float(np.clip(0.40 + (area / (h * w) * 5), 0.45, 0.90))
        
        detections.append({
            "class_name": cls,
            "confidence": conf,
            "bbox": [x, y, x + bw, y + bh],
            "area": int(area),
        })

    # Find crack contours
    contours_edge, _ = cv2.findContours(crack_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours_edge:
        area = cv2.contourArea(cnt)
        if area < min_area * 0.4:
            continue
        x, y, bw, bh = cv2.boundingRect(cnt)
        if bw == 0 or bh == 0:
            continue

        aspect = bw / max(bh, 1)
        rect_ratio = area / (bw * bh)
        
        # Calculate standard dev inside the contour
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(mask, [cnt], -1, 255, -1)
        _, std_dev = cv2.meanStdDev(gray, mask=mask)
        std_dev = float(std_dev[0][0])

        if std_dev < 4.0:
            continue
        if rect_ratio > 0.75 and 0.5 < aspect < 2.0:
            continue
        if y < h * 0.15:
            continue

        if aspect > 4.5:
            cls = "longitudinal_crack"
        elif aspect < 0.22:
            cls = "transverse_crack"
        else:
            cls = "crack"
        conf = float(np.clip(0.40 + (area / (h * w) * 6), 0.40, 0.85))
        
        detections.append({
            "class_name": cls,
            "confidence": conf,
            "bbox": [x, y, x + bw, y + bh],
            "area": int(area),
        })

    # Sort by confidence desc, keep top 6
    detections.sort(key=lambda d: d["confidence"], reverse=True)
    detections = detections[:6]

    # Remove overlapping boxes (basic NMS)
    detections = _nms(detections, iou_thresh=0.5)

    print(f"[Simulation] OpenCV found {len(detections)} region(s) after filtering")
    return detections


def _nms(detections: list, iou_thresh: float = 0.5) -> list:
    if not detections:
        return detections
    keep = []
    for i, d in enumerate(detections):
        dominated = False
        for j, k in enumerate(keep):
            if _iou(d["bbox"], k["bbox"]) > iou_thresh:
                dominated = True
                break
        if not dominated:
            keep.append(d)
    return keep


def _iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    if inter == 0:
        return 0.0
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return inter / (area_a + area_b - inter)


# ── Draw annotations ─────────────────────────────────────────────────────────
def _draw_annotations(img_bgr, detections):
    for det in detections:
        x1, y1, x2, y2 = det["bbox"]
        cls  = det["class_name"]
        conf = det["confidence"]
        meta  = DAMAGE_META.get(cls, {"color": (255, 255, 0),
                                      "label": cls.replace("_", " ").title()})
        color = meta["color"]
        label = f"{meta['label']} {conf * 100:.1f}%"

        cv2.rectangle(img_bgr, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        label_y = max(y1, th + 8)
        cv2.rectangle(img_bgr, (x1, label_y - th - 8), (x1 + tw + 6, label_y), color, -1)
        cv2.putText(img_bgr, label, (x1 + 3, label_y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)

    if not detections:
        cv2.putText(img_bgr, "No road damage detected.",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                    (40, 200, 80), 2, cv2.LINE_AA)

    cv2.putText(img_bgr, "RoadGuard AI",
                (10, img_bgr.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (100, 180, 255), 1, cv2.LINE_AA)
    return img_bgr


def is_simulation():
    return _simulation_mode
