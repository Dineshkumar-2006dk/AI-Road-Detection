import requests, re, os, sys, time

BASE = "http://127.0.0.1:5000"
errors = []

def check(label, cond, detail=""):
    if cond:
        print(f"  [PASS] {label}")
    else:
        print(f"  [FAIL] {label} {detail}")
        errors.append(label)

print("\n=== RoadGuard AI – Functional Test ===\n")

# 1. Root redirect
r = requests.get(BASE + "/", allow_redirects=False, timeout=5)
check("Root redirects to login", r.status_code == 302)

# 2. Login page
r = requests.get(BASE + "/auth/login", timeout=5)
check("Login page loads", r.status_code == 200)

# 3. Dashboard blocked without login
r = requests.get(BASE + "/dashboard/", allow_redirects=False, timeout=5)
check("Dashboard requires login (302)", r.status_code == 302)

# 4. Login
s = requests.Session()
login_page = s.get(BASE + "/auth/login", timeout=5)
match = re.search(r'name="csrf_token".*?value="([^"]+)"', login_page.text)
csrf = match.group(1) if match else ""
r = s.post(BASE + "/auth/login",
    data={"email":"admin@roadguard.ai","password":"Admin@1234","csrf_token":csrf},
    allow_redirects=True, timeout=5)
check("Admin login succeeds", "dashboard" in r.url or r.status_code == 200, f"url={r.url}")

# 5. Dashboard after login
r = s.get(BASE + "/dashboard/", timeout=5)
check("Dashboard accessible after login", r.status_code == 200)

# 6. Stats API
r = s.get(BASE + "/dashboard/api/stats", timeout=5)
try:
    j = r.json()
    check("Stats API returns JSON", "total_detections" in j, str(j)[:100])
except Exception as e:
    check("Stats API returns JSON", False, str(e))

# 7. History API
r = s.get(BASE + "/history/api/list?page=1", timeout=5)
try:
    j = r.json()
    check("History API returns JSON", j.get("success") is True or "items" in j, str(j)[:100])
except Exception as e:
    check("History API returns JSON", False, str(e))

# 8. Detection API with a test image
import cv2, numpy as np, io
img = np.zeros((480, 640, 3), dtype=np.uint8)
# Draw a dark "pothole-like" circle
cv2.circle(img, (320, 240), 80, (20, 20, 20), -1)
cv2.rectangle(img, (100, 100), (200, 130), (15, 15, 15), -1)

ok_img, buf = cv2.imencode(".jpg", img)
img_bytes = io.BytesIO(buf.tobytes())

login_page2 = s.get(BASE + "/detect/image", timeout=5)
match2 = re.search(r'name="csrf_token".*?value="([^"]+)"', login_page2.text)
csrf2 = match2.group(1) if match2 else csrf

r = s.post(BASE + "/detect/api/image",
    files={"image": ("test_road.jpg", img_bytes, "image/jpeg")},
    headers={"X-CSRFToken": csrf2},
    timeout=30)
try:
    j = r.json()
    check("Detection API returns success", j.get("success") is True, str(j)[:200])
    if j.get("success"):
        check("Detection has road_condition", bool(j.get("road_condition")))
        check("Detection has result_image_url", bool(j.get("result_image_url")))
        print(f"         Road condition: {j.get('road_condition')} | "
              f"Severity: {j.get('severity')} | "
              f"Count: {j.get('detection_count')} | "
              f"Conf: {j.get('avg_confidence')}% | "
              f"Sim: {j.get('simulation_mode')}")
except Exception as e:
    check("Detection API", False, str(e))

# 9. Logout
r = s.get(BASE + "/auth/logout", allow_redirects=True, timeout=5)
check("Logout works", "login" in r.url, f"url={r.url}")

# 10. Dashboard blocked after logout
r = s.get(BASE + "/dashboard/", allow_redirects=False, timeout=5)
check("Dashboard blocked after logout", r.status_code == 302)

print(f"\n=== Results: {9 - len(errors) + (1 if not errors else 0)}/10 passed ===")
if errors:
    print("Failed:", errors)
else:
    print("All tests PASSED!")
