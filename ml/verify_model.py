from ultralytics import YOLO
import sys

# Load the trained model
model_path = "runs/train_experiment/weights/best.pt"
try:
    model = YOLO(model_path) 
    print(f"✅ Model loaded successfully: {model_path}")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

# Verify Class Names
print("\n🔍 Model Classes (model.names):")
for id, name in model.names.items():
    print(f"  {id}: {name}")

# Test Inference
test_image = "datasets/final/images/30e7291bb314410983dbffe2c14d35d2.jpg"
print(f"\n🚀 Running Inference on: {test_image}")
results = model.predict(test_image, verbose=False)

# Show Detections
for result in results:
    print(f"Found {len(result.boxes)} object(s):")
    for box in result.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        label = model.names[cls_id]
        print(f"  - Label: {label} (ID: {cls_id}) | Conf: {conf:.4f}")

print("\n✅ Verification Complete.")
