import time
import sys
from ultralytics import YOLO

# Configuration
MODEL_PATH = "runs/train_refined/weights/best.pt"
TEST_IMAGE = "datasets/final/images/30e7291bb314410983dbffe2c14d35d2.jpg"
CONF_THRESHOLD = 0.01  # Low threshold for proof-of-load

print(f"🔄 Loading model from: {MODEL_PATH}")
try:
    start_load = time.time()
    model = YOLO(MODEL_PATH)
    load_time = (time.time() - start_load) * 1000
    print(f"✅ Model loaded in {load_time:.2f} ms")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

# Verify Class Names
print("\n🔍 Model Classes (model.names):")
if isinstance(model.names, dict):
    for id, name in model.names.items():
        print(f"  {id}: {name}")
else:
    print(f"❌ model.names is not a dict! Got: {type(model.names)}")
    print(model.names)

# Test Inference
print(f"\n🚀 Running Inference on: {TEST_IMAGE}")
try:
    start_infer = time.time()
    # Force CPU for consistent timing measurement in this environment, or let it auto-select
    results = model.predict(TEST_IMAGE, conf=CONF_THRESHOLD, verbose=False)
    latency = (time.time() - start_infer) * 1000
    print(f"⏱️ Inference Latency: {latency:.2f} ms")
except Exception as e:
    print(f"❌ Inference failed: {e}")
    sys.exit(1)

# Show Detections
for result in results:
    num_dets = len(result.boxes)
    print(f"\n📊 Detections Found: {num_dets}")
    
    if num_dets == 0:
        print("⚠️ No objects found. (Expected if model is under-trained or threshold too high)")
    
    for i, box in enumerate(result.boxes):
        # Extract details
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        label = model.names.get(cls_id, "Unknown")
        xyxy = box.xyxy[0].tolist()
        
        # Print optimized "Phase 3" output
        print(f"  [{i+1}] Label: {label} (ID: {cls_id})")
        print(f"      Conf : {conf:.4f}")
        print(f"      BBox : {[round(x, 2) for x in xyxy]} (xyxy pixel)")

print("\n✅ Verification Complete.")
