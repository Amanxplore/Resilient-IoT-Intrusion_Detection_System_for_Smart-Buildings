import json
import os
import tempfile
import numpy as np

FEEDBACK_FILE = "feedbackmemory.json"

def load_feedback(filepath=FEEDBACK_FILE):
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_feedback(feedback_memory, filepath=FEEDBACK_FILE):
    """Atomic write operation to prevent JSON corruption during high-frequency stream updates."""
    dir_name = os.path.dirname(filepath) or "."
    try:
        with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name, encoding="utf-8") as tf:
            json.dump(feedback_memory, tf, indent=4)
            temp_name = tf.name
        os.replace(temp_name, filepath)
    except Exception as e:
        print(f"Warning: Failed to save feedback memory atomically: {e}")

def add_feedback(features, label, filepath=FEEDBACK_FILE):
    memory = load_feedback(filepath)
    if isinstance(features, np.ndarray):
        features = features.tolist()
    memory.append({
        "features": features,
        "label": label,
        "match_count": 1
    })
    
    MAX_FEEDBACK = 150
    if len(memory) > MAX_FEEDBACK:
        memory.pop(0)
        
    save_feedback(memory, filepath)

def find_similar_feedback(current_features, feedback_memory, threshold=0.9):
    if not feedback_memory:
        return None
    
    current_features = np.asarray(current_features, dtype=np.float32)
    norm_c = np.linalg.norm(current_features)
    if norm_c == 0:
        return None

    for entry in feedback_memory:
        if entry.get("match_count", 0) > 50:
            continue
            
        stored_features = np.asarray(entry["features"], dtype=np.float32)
        if stored_features.shape != current_features.shape:
            continue
            
        norm_s = np.linalg.norm(stored_features)
        if norm_s == 0:
            continue
            
        similarity = np.dot(current_features, stored_features) / (norm_c * norm_s)
        if similarity > threshold:
            entry["match_count"] = entry.get("match_count", 0) + 1
            save_feedback(feedback_memory)
            print(f"Feedback similarity match: {similarity:.2f}")
            print(f"Feedback reused {entry['match_count']} times")
            return (entry["label"], float(similarity), entry["match_count"])
            
    return None
