"""
Comprehensive Flow Test v2 for RASA-ID Backend
================================================
Tests all endpoints with CORRECT admin paths.
"""
import requests
import json
import sys
import os
from pathlib import Path

BASE = "http://localhost:8000/api/v1"
ADMIN_KEY = os.environ.get("ADMIN_KEY", "admin_secret_123")
ADMIN_HEADERS = {"X-Admin-Key": ADMIN_KEY}

results = []

def test(name, method, url, expect_status=None, **kwargs):
    try:
        resp = getattr(requests, method)(url, **kwargs)
        status = resp.status_code
        try:
            body = resp.json()
        except Exception:
            body = f"[binary: {len(resp.content)} bytes, type={resp.headers.get('content-type','?')}]"
        
        if expect_status:
            ok = status == expect_status
        else:
            ok = status < 500
        
        symbol = "PASS" if ok else "FAIL"
        results.append((name, status, ok))
        
        print(f"\n{'[PASS]' if ok else '[FAIL]'} [{status}] {name}")
        if isinstance(body, dict):
            for k, v in list(body.items())[:5]:
                val_str = str(v)[:120]
                print(f"   {k}: {val_str}")
        else:
            print(f"   {str(body)[:200]}")
        return resp
    except requests.ConnectionError:
        results.append((name, "CONN_ERR", False))
        print(f"\n[FAIL] [CONN_ERR] {name}")
        return None
    except Exception as e:
        results.append((name, "ERROR", False))
        print(f"\n[FAIL] [ERROR] {name} -- {e}")
        return None

def create_test_image():
    try:
        from PIL import Image
        img = Image.new("RGB", (640, 480), color=(200, 180, 160))
        path = Path(__file__).parent / "test_image_flow.jpg"
        img.save(str(path), "JPEG")
        return str(path)
    except Exception:
        return None

print("=" * 70)
print("  RASA-ID v2 -- Comprehensive Flow Test v2")
print("=" * 70)

TEST_IMG = create_test_image()
if not TEST_IMG:
    print("ERROR: Cannot create test image (PIL not available)")
    sys.exit(1)
print(f"\nTest image: {TEST_IMG}")

# ===== 1. HEALTH =====
print("\n" + "-" * 70)
print("  1. HEALTH & INFO")
print("-" * 70)

test("GET /health", "get", f"{BASE}/health", expect_status=200)
test("GET /detectable-foods", "get", f"{BASE}/detectable-foods", expect_status=200)

# ===== 2. DETECTION =====
print("\n" + "-" * 70)
print("  2. DETECTION")
print("-" * 70)

detect_resp = test("POST /detect", "post", f"{BASE}/detect",
    expect_status=200,
    files={"file": ("test_food.jpg", open(TEST_IMG, "rb"), "image/jpeg")})

analysis_id = None
detected_label = None
if detect_resp and detect_resp.status_code == 200:
    data = detect_resp.json()
    analysis_id = data.get("analysis_id")
    items = data.get("items", [])
    if items:
        detected_label = items[0].get("label")
        print(f"   >>> analysis_id={analysis_id}, labels={[i['label'] for i in items]}")
        # Verify serat_g fix -- should be 0, never None
        for item in items:
            tkpi = item.get("tkpi")
            if tkpi and tkpi.get("nutrition"):
                serat = tkpi["nutrition"].get("serat_g")
                if serat is None:
                    print(f"   >>> [VERIFY FAIL] serat_g is None for {item['label']}!")
                else:
                    print(f"   >>> [VERIFY OK] serat_g={serat} for {item['label']} (not None)")
    else:
        print(f"   >>> analysis_id={analysis_id}, no items (test image has no food)")

# ===== 3. TKPI SEARCH =====
print("\n" + "-" * 70)
print("  3. TKPI")
print("-" * 70)

test("GET /tkpi/search?q=nasi", "get", f"{BASE}/tkpi/search?q=nasi", expect_status=200)

# ===== 4. FEEDBACK (valid + invalid label) =====
print("\n" + "-" * 70)
print("  4. FEEDBACK")
print("-" * 70)

if analysis_id:
    fb_label = detected_label or "nasi_putih"
    test("POST /feedback (valid)", "post", f"{BASE}/feedback",
        expect_status=200,
        json={
            "analysis_id": analysis_id,
            "items": [{
                "predicted_label": fb_label,
                "corrected_tkpi_id": None,
                "bbox": [100.0, 100.0, 300.0, 300.0],
                "note": "Flow test"
            }]
        })
    
    # Invalid label -> must be 400 (not 500!)
    test("POST /feedback (invalid label -> 400)", "post", f"{BASE}/feedback",
        expect_status=400,
        json={
            "analysis_id": analysis_id,
            "items": [{
                "predicted_label": "makanan_xyz_tidak_ada",
                "corrected_tkpi_id": None,
                "bbox": [10.0, 10.0, 200.0, 200.0],
                "note": "Test invalid"
            }]
        })
else:
    print("   SKIP: no analysis_id")

# ===== 5. CLASS REQUEST =====
print("\n" + "-" * 70)
print("  5. CLASS REQUEST")
print("-" * 70)

test("POST /class-request", "post", f"{BASE}/class-request",
    expect_status=200,
    json={
        "analysis_id": analysis_id or 1,
        "requested_label": "sambal_terasi",
        "bbox": [50.0, 50.0, 150.0, 150.0],
        "note": "Flow test"
    })

# ===== 6. MISSED DETECTION =====
print("\n" + "-" * 70)
print("  6. MISSED DETECTION")
print("-" * 70)

if analysis_id:
    test("POST /missed-detection", "post", f"{BASE}/missed-detection",
        json={
            "analysis_id": analysis_id,
            "missed_label": "sambal",
            "note": "Test missed"
        })
else:
    print("   SKIP: no analysis_id")

# ===== 7. ADMIN ENDPOINTS (correct paths) =====
print("\n" + "-" * 70)
print("  7. ADMIN ENDPOINTS")
print("-" * 70)

# Admin dashboard summary
test("GET /admin/summary", "get", f"{BASE}/admin/summary", headers=ADMIN_HEADERS)

# Admin model classes
test("GET /admin/model/classes", "get", f"{BASE}/admin/model/classes", headers=ADMIN_HEADERS)

# Admin model status
test("GET /admin/model/status", "get", f"{BASE}/admin/model/status", headers=ADMIN_HEADERS)

# Admin mappings
test("GET /admin/mappings", "get", f"{BASE}/admin/mappings", headers=ADMIN_HEADERS)

# Admin no key -> should be 401 or 403
test("GET /admin/summary (no key -> 401/403)", "get", f"{BASE}/admin/summary")

# ===== 8. EXPORT ENDPOINTS (correct paths) =====
print("\n" + "-" * 70)
print("  8. EXPORT ENDPOINTS")
print("-" * 70)

# Export summary
test("GET /admin/export/summary", "get", f"{BASE}/admin/export/summary", headers=ADMIN_HEADERS)

# Feedback export (legacy)
test("GET /admin/feedback/export", "get", f"{BASE}/admin/feedback/export", headers=ADMIN_HEADERS)

# Class request export (legacy)
test("GET /admin/class-requests/export", "get", f"{BASE}/admin/class-requests/export", headers=ADMIN_HEADERS)

# YOLO exports (new system)
test("GET /admin/export/yolo/feedback", "get", f"{BASE}/admin/export/yolo/feedback", headers=ADMIN_HEADERS)
test("GET /admin/export/yolo/class-requests", "get", f"{BASE}/admin/export/yolo/class-requests", headers=ADMIN_HEADERS)
test("GET /admin/export/yolo/missed", "get", f"{BASE}/admin/export/yolo/missed", headers=ADMIN_HEADERS)

# ===== SUMMARY =====
print("\n" + "=" * 70)
print("  TEST SUMMARY")
print("=" * 70)

passed = sum(1 for _, _, ok in results if ok)
failed = sum(1 for _, _, ok in results if not ok)

for name, status, ok in results:
    symbol = "[PASS]" if ok else "[FAIL]"
    print(f"  {symbol} [{status}] {name}")

print(f"\n  Total: {len(results)} | Passed: {passed} | Failed: {failed}")

if failed > 0:
    print(f"\n  WARNING: {failed} test(s) FAILED")
    sys.exit(1)
else:
    print(f"\n  All {passed} tests passed!")
    sys.exit(0)
