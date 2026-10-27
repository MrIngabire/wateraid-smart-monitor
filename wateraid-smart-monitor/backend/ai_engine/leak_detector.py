"""
AI/ML Engine for Pipeline Leak Detection
Uses Isolation Forest + rule-based anomaly detection
"""
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, 'leak_detector_model.pkl')
SCALER_PATH = os.path.join(MODEL_DIR, 'scaler.pkl')


class LeakDetector:
    """
    Hybrid leak detection:
    1. Rule-based threshold checking (immediate)
    2. Isolation Forest ML model (pattern-based)
    """
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self._load_or_train()
    
    def _load_or_train(self):
        """Load existing model or train a new one"""
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.scaler = joblib.load(SCALER_PATH)
                print("[AI] Loaded existing leak detector model.")
                return
            except Exception as e:
                print(f"[AI] Failed to load model: {e}. Training new one...")
        
        self._train_baseline_model()
    
    def _train_baseline_model(self):
        """
        Train an Isolation Forest on synthetic baseline data.
        In production, this would use historical sensor data.
        """
        print("[AI] Training baseline leak detector model...")
        
        np.random.seed(42)
        n_samples = 5000
        
        # Normal operation data
        normal_flow = np.random.normal(42.0, 2.0, n_samples)
        normal_pressure = np.random.normal(350.0, 10.0, n_samples)
        
        # Anomalous data (leaks)
        n_anomalies = 500
        leak_flow = np.random.normal(60.0, 5.0, n_anomalies)  # sudden flow spike
        leak_pressure = np.random.normal(250.0, 20.0, n_anomalies)  # pressure drop
        
        X_normal = np.column_stack([normal_flow, normal_pressure])
        X_anomaly = np.column_stack([leak_flow, leak_pressure])
        X = np.vstack([X_normal, X_anomaly])
        
        # Fit scaler
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_scaled)
        
        # Save
        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.scaler, SCALER_PATH)
        print("[AI] Model trained and saved successfully.")
    
    def predict(self, flow_rate, pressure, baseline_flow=42.0, baseline_pressure=350.0):
        """
        Returns dict with:
        - is_anomaly: bool
        - confidence: float (0-1)
        - anomaly_type: str
        - message: str
        """
        # Rule-based check (fast path)
        flow_deviation = abs(flow_rate - baseline_flow) / baseline_flow
        pressure_deviation = abs(pressure - baseline_pressure) / baseline_pressure
        
        # ML prediction
        X = np.array([[flow_rate, pressure]])
        X_scaled = self.scaler.transform(X)
        ml_prediction = self.model.predict(X_scaled)[0]  # 1=normal, -1=anomaly
        anomaly_score = -self.model.score_samples(X_scaled)[0]  # higher = more anomalous
        
        # Normalize score to 0-1 confidence
        confidence = min(1.0, max(0.0, (anomaly_score + 0.5) / 1.5))
        
        is_anomaly = False
        anomaly_type = None
        message = "Pipeline operating normally."
        
        # Decision logic
        if pressure_deviation > 0.15 and flow_deviation > 0.20:
            is_anomaly = True
            anomaly_type = 'LEAK'
            message = f"Critical leak detected: {pressure_deviation*100:.1f}% pressure drop with {flow_deviation*100:.1f}% flow anomaly."
            confidence = max(confidence, 0.90)
        elif pressure_deviation > 0.10:
            is_anomaly = True
            anomaly_type = 'PRESSURE_DROP'
            message = f"Abnormal pressure drop detected: {pressure_deviation*100:.1f}% below baseline."
            confidence = max(confidence, 0.75)
        elif flow_deviation > 0.25:
            is_anomaly = True
            anomaly_type = 'FLOW_ANOMALY'
            message = f"Flow rate anomaly: {flow_deviation*100:.1f}% deviation from baseline."
            confidence = max(confidence, 0.70)
        elif ml_prediction == -1 and confidence > 0.6:
            is_anomaly = True
            anomaly_type = 'MAINTENANCE'
            message = "Predictive maintenance recommended based on ML pattern analysis."
        
        return {
            'is_anomaly': is_anomaly,
            'confidence': round(confidence, 4),
            'anomaly_type': anomaly_type,
            'message': message,
            'flow_deviation_pct': round(flow_deviation * 100, 2),
            'pressure_deviation_pct': round(pressure_deviation * 100, 2),
        }


# Singleton instance
_detector_instance = None

def get_detector():
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = LeakDetector()
    return _detector_instance