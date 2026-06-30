"""
GPS & Mapping Utilities
========================
Reverse geocoding via Geopy, Google Maps link generation, Folium map builder.
"""

import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from flask import current_app


# ── Reverse geocoding ────────────────────────────────────────────────────────
def reverse_geocode(lat: float, lon: float) -> str:
    """Return human-readable address for coordinates."""
    try:
        geolocator = Nominatim(user_agent="roadguard_ai_v1")
        location   = geolocator.reverse((lat, lon), timeout=5)
        return location.address if location else f"{lat:.5f}, {lon:.5f}"
    except GeocoderTimedOut:
        return f"{lat:.5f}, {lon:.5f}"
    except Exception:
        return f"{lat:.5f}, {lon:.5f}"


def google_maps_link(lat: float, lon: float) -> str:
    """Generate a Google Maps link for the given coordinates."""
    return f"https://www.google.com/maps?q={lat},{lon}"


# ── Folium interactive map ────────────────────────────────────────────────────
CONDITION_ICONS = {
    "Good":     ("green",  "check"),
    "Moderate": ("orange", "exclamation-triangle"),
    "Poor":     ("orange", "exclamation-circle"),
    "Critical": ("red",    "times-circle"),
}


def build_folium_map(detections: list) -> str:
    """
    Build an interactive Folium map with all detections.

    Parameters
    ----------
    detections : list of Detection ORM objects (with lat/lon attributes)

    Returns
    -------
    HTML string of the rendered map.
    """
    cfg = current_app.config
    center_lat = cfg.get("DEFAULT_MAP_CENTER_LAT", 11.0168)
    center_lon = cfg.get("DEFAULT_MAP_CENTER_LON", 76.9558)

    # Auto-center on detections if available
    valid = [d for d in detections if d.latitude and d.longitude]
    if valid:
        center_lat = sum(d.latitude  for d in valid) / len(valid)
        center_lon = sum(d.longitude for d in valid) / len(valid)

    fmap = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles="CartoDB dark_matter",
    )

    # Layer groups
    layers = {
        "Good":     folium.FeatureGroup(name="Good Roads",    show=True),
        "Moderate": folium.FeatureGroup(name="Moderate Roads",show=True),
        "Poor":     folium.FeatureGroup(name="Poor Roads",    show=True),
        "Critical": folium.FeatureGroup(name="Critical Roads",show=True),
    }

    for det in valid:
        condition = det.road_condition or "Poor"
        icon_color, icon_name = CONDITION_ICONS.get(condition, ("gray", "question"))
        damage_list = ", ".join(det.get_damage_types()) or "Unknown"

        popup_html = f"""
        <div style="min-width:220px;font-family:Arial,sans-serif;">
          <h5 style="color:#2196F3;margin:4px 0;">RoadGuard AI</h5>
          <hr style="margin:4px 0;">
          <b>Condition:</b> {condition}<br>
          <b>Severity:</b>  {det.severity or "N/A"}<br>
          <b>Damage:</b>    {damage_list}<br>
          <b>Confidence:</b>{det.avg_confidence*100:.1f}%<br>
          <b>Time:</b>      {det.timestamp.strftime('%Y-%m-%d %H:%M') if det.timestamp else 'N/A'}<br>
          <b>Location:</b>  {det.location_name or f"{det.latitude:.4f}, {det.longitude:.4f}"}<br>
          <a href="{det.maps_link or '#'}" target="_blank"
             style="color:#2196F3;">Open in Google Maps ↗</a>
        </div>
        """

        marker = folium.Marker(
            location=[det.latitude, det.longitude],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{condition} – {damage_list[:40]}",
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa"),
        )

        layer = layers.get(condition, layers["Poor"])
        marker.add_to(layer)

    for layer in layers.values():
        layer.add_to(fmap)

    # ── Togglable Damage Heatmap Layer ──────────────────────────────────────────
    try:
        from folium.plugins import HeatMap
        heat_data = []
        for det in valid:
            condition = det.road_condition or "Poor"
            w = 1.0 if condition == "Critical" else (0.7 if condition == "Poor" else (0.4 if condition == "Moderate" else 0.1))
            heat_data.append([det.latitude, det.longitude, w])
        if heat_data:
            HeatMap(heat_data, name="Damage Heatmap", show=False, radius=18, blur=12, min_opacity=0.4).add_to(fmap)
    except Exception as e:
        if 'logger' in locals() or 'current_app' in locals():
            current_app.logger.error(f"Failed to add HeatMap layer: {e}")

    folium.LayerControl(collapsed=False).add_to(fmap)

    # Minimap
    try:
        from folium.plugins import MiniMap
        MiniMap(toggle_display=True).add_to(fmap)
    except Exception:
        pass

    return fmap._repr_html_()
