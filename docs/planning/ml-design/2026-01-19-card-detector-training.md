# ML Design: Card Detection Training Pipeline

**Date:** 2026-01-19
**Feature:** Phase 2 - YOLOv8 Card Detector Training
**Author:** Alexios (ML Architecture) / Dulcy (Training Pipeline)

---

## 1. Problem Definition

### Objective
Train a YOLOv8 object detection model to recognize 159 unique playing cards from the CartesSociete game with high accuracy for mobile deployment.

### Success Criteria
| Metric | Target | Rationale |
|--------|--------|-----------|
| mAP@0.5 | > 90% | High precision required for gameplay |
| mAP@0.5:0.95 | > 75% | Good localization across IoU thresholds |
| Inference time | < 500ms | Smooth UX on mid-range Android |
| Model size | 50-100MB | Reasonable download size |

### Constraints
- 159 classes (fixed by card repository)
- Mobile deployment target (ONNX Runtime)
- Synthetic training data (from Phase 1)
- Transfer learning from COCO weights

---

## 2. Architecture Design

### Model Selection: YOLOv8n/s

| Variant | Params | mAP@COCO | Speed | Recommendation |
|---------|--------|----------|-------|----------------|
| YOLOv8n | 3.2M | 37.3 | Fastest | Mobile-first |
| YOLOv8s | 11.2M | 44.9 | Fast | Balanced |
| YOLOv8m | 25.9M | 50.2 | Medium | Accuracy-first |

**Decision:** Start with YOLOv8s for balanced accuracy/speed, with fallback to YOLOv8n if mobile constraints aren't met.

### Training Strategy

```
Phase 1: Feature Extraction (Frozen backbone)
├── Epochs: 10
├── Learning rate: 0.01
└── Purpose: Adapt head to card detection

Phase 2: Fine-tuning (Full model)
├── Epochs: 100
├── Learning rate: 0.001 -> 0.0001 (cosine)
└── Purpose: Domain-specific optimization

Phase 3: Optimization
├── Quantization: INT8
├── Pruning: Structured (optional)
└── Purpose: Mobile deployment
```

### Data Pipeline

```
data/training/
├── images/
│   ├── train/    # 80% of augmented images
│   └── val/      # 20% of augmented images
├── labels/
│   ├── train/    # YOLO format annotations
│   └── val/
└── data.yaml     # Class mapping (159 classes)
```

---

## 3. Training Configuration

### Hyperparameters

```yaml
# Model
model: yolov8s.pt
imgsz: 640
batch: 16  # Adjust based on GPU memory

# Training
epochs: 100
patience: 20  # Early stopping
optimizer: AdamW
lr0: 0.001
lrf: 0.01  # Final LR = lr0 * lrf
momentum: 0.937
weight_decay: 0.0005

# Augmentation (in addition to Phase 1)
augment: true
hsv_h: 0.015
hsv_s: 0.7
hsv_v: 0.4
degrees: 0  # Already applied in Phase 1
translate: 0.1
scale: 0.5
fliplr: 0.0  # Cards shouldn't be flipped
flipud: 0.0
mosaic: 0.5  # 4-card composites
mixup: 0.1

# Validation
val: true
plots: true
```

### Loss Function
- Box loss (CIoU): Bounding box regression
- Classification loss (BCE): Multi-class card identification
- DFL loss: Distribution focal loss for precise localization

---

## 4. Mobile Optimization

### Quantization Strategy

```python
# Post-training quantization
model.export(format='onnx', int8=True, dynamic=True)
```

| Precision | Size Reduction | Accuracy Impact |
|-----------|----------------|-----------------|
| FP32 | Baseline | Baseline |
| FP16 | ~50% | < 0.5% mAP loss |
| INT8 | ~75% | 1-2% mAP loss |

### ONNX Export

```python
# Export with optimizations
model.export(
    format='onnx',
    imgsz=640,
    simplify=True,
    opset=17,
    dynamic=True,  # Variable batch size
)
```

### Mobile Runtime Options
1. **ONNX Runtime Mobile** - Primary target
2. **TensorFlow Lite** - Alternative if needed
3. **CoreML** - iOS future support

---

## 5. Evaluation Protocol

### Metrics to Track
- mAP@0.5, mAP@0.5:0.95
- Precision, Recall per class
- Inference latency (GPU, CPU, mobile)
- Model size (FP32, FP16, INT8)

### Validation Strategy
- Hold-out validation set (20% from Phase 1)
- Per-family performance analysis
- Confusion matrix for similar cards
- Real-world image testing (post-training)

---

## 6. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Class imbalance | Weighted sampling, focal loss |
| Similar cards confusion | Increase augmentation variety |
| Mobile inference too slow | Fall back to YOLOv8n |
| Overfitting to synthetic data | Aggressive augmentation, early stopping |

---

## 7. Implementation Checklist

- [x] Phase 1: Data pipeline complete
- [ ] Add ultralytics dependency
- [ ] Create training configuration
- [ ] Implement training script
- [ ] Implement ONNX export script
- [ ] Create inference wrapper
- [ ] Add unit tests
- [ ] Validate on test set
- [ ] Export optimized ONNX model
