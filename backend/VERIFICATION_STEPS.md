# Verification Steps for Feedback Storage

## 1. Test via cURL

### Submit Feedback
```bash
curl -X POST "http://localhost:8000/api/v1/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": 1,
    "items": [
      {
        "bbox": [100, 150, 300, 400],
        "predicted_label": "nasi",
        "corrected_tkpi_id": 1,
        "note": "Test feedback via cURL"
      }
    ]
  }'
```

**Expected Response:**
```json
{
  "ok": true,
  "saved": 1,
  "message": "Successfully saved 1 feedback items"
}
```

**Expected Console Output:**
```
✅ Feedback image copied: feedback/images/<uuid>.jpg
✅ Label file created: feedback/labels/<uuid>.txt
✅ Saved 1 feedback items to database
```

---

## 2. Verify Database Records

### Check Latest Feedback Record
```sql
SELECT 
    id,
    analysis_id,
    predicted_label,
    corrected_tkpi_food_id,
    bbox_x1, bbox_y1, bbox_x2, bbox_y2,
    note,
    is_processed,
    created_at
FROM feedback
ORDER BY created_at DESC
LIMIT 1;
```

**Expected Result:**
```
id: 1
analysis_id: 1
predicted_label: nasi
corrected_tkpi_food_id: 1
bbox_x1: 100
bbox_y1: 150
bbox_x2: 300
bbox_y2: 400
note: Test feedback via cURL
is_processed: false
created_at: 2026-01-17 13:50:00
```

### Check All Feedback Records
```sql
SELECT COUNT(*) as total_feedback FROM feedback;
```

---

## 3. Verify File System

### Check Feedback Image Files
```bash
# Windows (PowerShell)
Get-ChildItem -Path "storage\feedback\images" -Recurse

# Linux/Mac
ls -lah storage/feedback/images/
```

**Expected Output:**
```
storage/feedback/images/<uuid>.jpg  (copied from analysis)
```

### Check Label Files
```bash
# Windows (PowerShell)
Get-ChildItem -Path "storage\feedback\labels" -Recurse

# Linux/Mac
ls -lah storage/feedback/labels/
```

**Expected Output:**
```
storage/feedback/labels/<uuid>.txt  (same UUID as image)
```

### View Label File Content
```bash
# Windows
type storage\feedback\labels\<uuid>.txt

# Linux/Mac
cat storage/feedback/labels/<uuid>.txt
```

**Expected Content:**
```
# TODO: Normalize bbox with image dimensions
# Raw bbox: 100 150 300 400
# Class ID: 0
0 0.5 0.5 0.1 0.1
```

---

## 4. Verify Path Format

All paths should be **POSIX-style** (forward slashes):
- ✅ `feedback/images/abc123.jpg`
- ❌ `feedback\images\abc123.jpg`

### Check in Database
```sql
SELECT image_path FROM analyses ORDER BY created_at DESC LIMIT 1;
```

Should return: `uploads/2026/01/17/<uuid>.jpg` (not backslashes)

---

## 5. Complete Workflow Test

### Step 1: Upload and Detect
```bash
curl -X POST "http://localhost:8000/api/v1/detection/photo" \
  -F "file=@test_image.jpg"
```

Save the `analysis_id` from response.

### Step 2: Submit Feedback
```bash
curl -X POST "http://localhost:8000/api/v1/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "analysis_id": <analysis_id>,
    "items": [
      {
        "bbox": [50, 75, 200, 250],
        "predicted_label": "tempe",
        "corrected_tkpi_id": null,
        "note": "Deteksi salah, bukan tempe"
      }
    ]
  }'
```

### Step 3: Verify Files Created
```bash
# Check console output for paths
# Check database for feedback record
# Check filesystem for image and label files
```

---

## 6. Troubleshooting

### Issue: "Analysis not found"
**Solution:** Make sure analysis_id exists in database
```sql
SELECT id FROM analyses ORDER BY created_at DESC LIMIT 5;
```

### Issue: "TKPI food not found"
**Solution:** Either set `corrected_tkpi_id` to `null` or use valid TKPI ID
```sql
SELECT id, name FROM tkpi_foods LIMIT 5;
```

### Issue: Files not created
**Solution:** Check console output for error messages and verify storage path permissions

### Issue: Paths with backslashes
**Solution:** All path functions use `Path(...).as_posix()` to ensure forward slashes

---

## 7. Quick Verification Checklist

- [ ] POST /feedback returns 200 OK
- [ ] Console shows: "✅ Feedback image copied: ..."
- [ ] Console shows: "✅ Label file created: ..."
- [ ] Console shows: "✅ Saved N feedback items to database"
- [ ] Database has new row in `feedback` table
- [ ] File exists: `storage/feedback/images/<uuid>.jpg`
- [ ] File exists: `storage/feedback/labels/<uuid>.txt`
- [ ] Label filename matches image filename (same UUID)
- [ ] All paths use forward slashes (POSIX)
- [ ] Folders created automatically if missing
