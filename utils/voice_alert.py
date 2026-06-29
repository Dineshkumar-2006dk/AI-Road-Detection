"""
Voice Alert Utility
====================
Speaks road damage alerts in English or Tamil using pyttsx3 (offline TTS).
Runs in a background thread so Flask is never blocked.
"""

import threading

_MESSAGES_EN = {
    "pothole":            "Warning! Pothole detected ahead. Reduce vehicle speed.",
    "crack":              "Road crack detected. Proceed with caution.",
    "longitudinal_crack": "Longitudinal crack detected. Drive carefully.",
    "transverse_crack":   "Transverse crack detected. Reduce speed.",
    "alligator_crack":    "Alligator cracking detected. Severe road damage ahead.",
    "surface_damage":     "Road surface damage detected.",
    "road_edge_failure":  "Road edge failure detected. Stay away from road edges.",
    "road_depression":    "Road depression detected. Slow down.",
    "patch_failure":      "Patch failure detected. Uneven road surface ahead.",
    "water_logging":      "Water logging detected. Drive with extreme caution.",
    "loose_gravel":       "Loose gravel detected. Reduce speed and grip the steering.",
    "good":               "Road condition is good. Safe to drive.",
    "moderate":           "Moderate road damage detected. Proceed with caution.",
    "poor":               "Poor road condition detected. Reduce vehicle speed.",
    "critical":           "Critical road damage! Reduce vehicle speed immediately.",
}

_MESSAGES_TA = {
    "pothole":            "எச்சரிக்கை! குழி கண்டுபிடிக்கப்பட்டது. வேகத்தை குறைக்கவும்.",
    "crack":              "சாலை வெடிப்பு கண்டுபிடிக்கப்பட்டது. எச்சரிக்கையாக ஓட்டவும்.",
    "critical":           "மிகவும் ஆபத்தான சாலை சேதம்! உடனே வேகத்தை குறைக்கவும்.",
    "poor":               "மோசமான சாலை நிலை. வேகத்தை குறைக்கவும்.",
    "moderate":           "மிதமான சாலை சேதம். எச்சரிக்கையாக செல்லவும்.",
    "good":               "சாலை நிலை நல்லது. பாதுகாப்பாக ஓட்டலாம்.",
}


def _get_language():
    try:
        from flask import current_app
        return current_app.config.get("VOICE_LANGUAGE", "en")
    except RuntimeError:
        return "en"


def speak_alert(damage_class_or_condition: str):
    """
    Play a voice alert in a background thread.
    damage_class_or_condition: damage class name (e.g. 'pothole') or
                                road condition (e.g. 'critical')
    """
    key = damage_class_or_condition.lower().replace(" ", "_")
    lang = _get_language()

    if lang == "ta":
        text = _MESSAGES_TA.get(key) or _MESSAGES_EN.get(key) or _MESSAGES_EN["poor"]
    else:
        text = _MESSAGES_EN.get(key) or _MESSAGES_EN["poor"]

    thread = threading.Thread(target=_speak, args=(text,), daemon=True)
    thread.start()
    print(f"[Voice] Playing alert ({lang}): {text[:60]}...")


def _speak(text: str):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate",   160)
        engine.setProperty("volume", 1.0)
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as exc:
        print(f"[Voice] pyttsx3 error: {exc}")
