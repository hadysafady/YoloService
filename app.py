import time
from collections import Counter
from fastapi import FastAPI, Security, UploadFile, File, HTTPException, Request ,Depends, status
from fastapi.responses import FileResponse, Response
from ultralytics import YOLO
from PIL import Image
import sqlite3
import os
import uuid
import shutil
from fastapi.security import HTTPBasic, HTTPBasicCredentials

# Disable GPU usage
import torch
torch.cuda.is_available = lambda: False

app = FastAPI()

UPLOAD_DIR = "uploads/original"
PREDICTED_DIR = "uploads/predicted"
DB_PATH = "predictions.db"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PREDICTED_DIR, exist_ok=True)

# Download the AI model (tiny model ~6MB)
model = YOLO("yolov8n.pt")  

# Initialize SQLite
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        # Create the predictions main table to store the prediction session
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prediction_sessions (
                uid TEXT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                original_image TEXT,
                predicted_image TEXT
            )
        """)
        
        # Create the objects table to store individual detected objects in a given image
        conn.execute("""
            CREATE TABLE IF NOT EXISTS detection_objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_uid TEXT,
                label TEXT,
                score REAL,
                box TEXT,
                FOREIGN KEY (prediction_uid) REFERENCES prediction_sessions (uid)
            )
        """)

        # Create users table
        conn.execute(""" 
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT   
            )
        """)

        # Adding username and password
        conn.execute("""
            INSERT or IGNORE INTO users (username,password) VALUES (?,?)
            """, ('hadyy','safadyy'))
        
        # Create index for faster queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_prediction_uid ON detection_objects (prediction_uid)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_label ON detection_objects (label)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_score ON detection_objects (score)")

init_db()

security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT password FROM users WHERE username = ?", 
            (credentials.username,)
        )
        row = cursor.fetchone()
    
    if row is None or row[0] != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username


def save_prediction_session(uid, original_image, predicted_image):
    """
    Save prediction session to database
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO prediction_sessions (uid, original_image, predicted_image)
            VALUES (?, ?, ?)
        """, (uid, original_image, predicted_image))

def save_detection_object(prediction_uid, label, score, box):
    """
    Save detection object to database
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO detection_objects (prediction_uid, label, score, box)
            VALUES (?, ?, ?, ?)
        """, (prediction_uid, label, score, str(box)))

optional_security = HTTPBasic(auto_error=False)
@app.post("/predict")
def predict(file: UploadFile = File(...),credentials: HTTPBasicCredentials = Security(optional_security)):
    username = None
    if credentials:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute(
                "SELECT password FROM users WHERE username = ?", 
                (credentials.username,)
            )
            row = cursor.fetchone()
        if row and row[0] == credentials.password:
            username = credentials.username
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Basic"},)

    """
    Predict objects in an image
    """
    start_time = time.time()
    ext = os.path.splitext(file.filename)[1]
    uid = str(uuid.uuid4())
    original_path = os.path.join(UPLOAD_DIR, uid + ext)
    predicted_path = os.path.join(PREDICTED_DIR, uid + ext)

    with open(original_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    results = model(original_path, device="cpu")

    annotated_frame = results[0].plot()  # NumPy image with boxes
    annotated_image = Image.fromarray(annotated_frame)
    annotated_image.save(predicted_path)

    save_prediction_session(uid, original_path, predicted_path)
    
    detected_labels = []
    for box in results[0].boxes:
        label_idx = int(box.cls[0].item())
        label = model.names[label_idx]
        score = float(box.conf[0])
        bbox = box.xyxy[0].tolist()
        save_detection_object(uid, label, score, bbox)
        detected_labels.append(label)

    processing_time = round(time.time() - start_time, 2)

    return {
        "prediction_uid": uid, 
        "detection_count": len(results[0].boxes),
        "labels": detected_labels,
        "time_took": processing_time
    }

@app.get("/predictions/count")
def get_prediction_count(username: str = Depends(authenticate)):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            SELECT COUNT(*) FROM prediction_sessions
            WHERE timestamp >= datetime('now', '-7 days')
        """)
        count = cursor.fetchone()[0]
    return count


@app.get("/prediction/{uid}")
def get_prediction_by_uid(uid: str, username: str = Depends(authenticate)):
    """
    Get prediction session by uid with all detected objects
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        # Get prediction session
        session = conn.execute("SELECT * FROM prediction_sessions WHERE uid = ?", (uid,)).fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Prediction not found")
            
        # Get all detection objects for this prediction
        objects = conn.execute(
            "SELECT * FROM detection_objects WHERE prediction_uid = ?", 
            (uid,)
        ).fetchall()
        
        return {
            "uid": session["uid"],
            "timestamp": session["timestamp"],
            "original_image": session["original_image"],
            "predicted_image": session["predicted_image"],
            "detection_objects": [
                {
                    "id": obj["id"],
                    "label": obj["label"],
                    "score": obj["score"],
                    "box": obj["box"]
                } for obj in objects
            ]
        }
@app.get("/labels")
def get_labels_last_week(username: str = Depends(authenticate)):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            SELECT DISTINCT do.label
            FROM detection_objects do
            JOIN prediction_sessions ps ON do.prediction_uid = ps.uid
            WHERE ps.timestamp >= datetime('now', '-7 days')
        """)
        labels = [row[0] for row in cursor.fetchall()]
    return labels


labels = [
   "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]
@app.get("/predictions/label/{label}")
def get_predictions_by_label(label: str, username: str = Depends(authenticate)):
    """
    Get prediction sessions containing objects with specified label
    """
    if label not in labels:
        raise HTTPException(status_code=400, detail="Invalid image type")
        
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT DISTINCT ps.uid, ps.timestamp
            FROM prediction_sessions ps
            JOIN detection_objects do ON ps.uid = do.prediction_uid
            WHERE do.label = ?
        """, (label,)).fetchall()
        
        return [{"uid": row["uid"], "timestamp": row["timestamp"]} for row in rows]

@app.get("/predictions/score/{min_score}")
def get_predictions_by_score(min_score: float, username: str = Depends(authenticate)):
    """
    Get prediction sessions containing objects with score >= min_score
    """
    if not 0 < min_score < 1 :
        raise HTTPException(status_code=400, detail="Score most be between 0 and 1")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT DISTINCT ps.uid, ps.timestamp
            FROM prediction_sessions ps
            JOIN detection_objects do ON ps.uid = do.prediction_uid
            WHERE do.score >= ?
        """, (min_score,)).fetchall()
        
        return [{"uid": row["uid"], "timestamp": row["timestamp"]} for row in rows]

@app.get("/image/{type}/{filename}")
def get_image(type: str, filename: str, username: str = Depends(authenticate)):
    """
    Get image by type and filename
    """
    if type not in ["original", "predicted"]:
        raise HTTPException(status_code=400, detail="Invalid image type")
    path = os.path.join("uploads", type, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)

@app.delete("/prediction/{uid}")
def delete_prediction(uid: str, username: str = Depends(authenticate)):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        session = conn.execute(
            "SELECT * FROM prediction_sessions WHERE uid = ?",
            (uid,)
        ).fetchone()

        if not session:
            raise HTTPException(status_code=404, detail="Prediction not found")

        conn.execute(
            "DELETE FROM detection_objects WHERE prediction_uid = ?",
            (uid,)
        )

        conn.execute(
            "DELETE FROM prediction_sessions WHERE uid = ?",
            (uid,)
        )

    for file_path in [session["original_image"], session["predicted_image"]]:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    return {"detail": f"Prediction {uid} deleted successfully"}


@app.get("/prediction/{uid}/image")
def get_prediction_image(uid: str, request: Request, username: str = Depends(authenticate)):
    """
    Get prediction image by uid
    """
    accept = request.headers.get("accept", "")
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT predicted_image FROM prediction_sessions WHERE uid = ?", (uid,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Prediction not found")
        image_path = row[0]

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Predicted image file not found")

    if "image/png" in accept:
        return FileResponse(image_path, media_type="image/png")
    elif "image/jpeg" in accept or "image/jpg" in accept:
        return FileResponse(image_path, media_type="image/jpeg")
    else:
        # If the client doesn't accept image, respond with 406 Not Acceptable
        raise HTTPException(status_code=406, detail="Client does not accept an image format")

@app.get("/health")
def health():
    """
    Health check endpoint
    """
    return {"status": "ok"}
 
@app.get("/stats")
def get_overall_stats(username: str = Depends(authenticate)):
    with sqlite3.connect(DB_PATH) as conn:
        cursor_cnt = conn.execute("""
            SELECT COUNT(*) FROM prediction_sessions
            WHERE timestamp >= datetime('now', '-7 days')
        """)
        total_predictions = cursor_cnt.fetchone()[0]

        cursor_scores = conn.execute("""
            SELECT do.score
            FROM detection_objects do
            JOIN prediction_sessions ps ON do.prediction_uid = ps.uid
            WHERE ps.timestamp >= datetime('now', '-7 days')
        """)
        all_scores = [row[0] for row in cursor_scores]
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

        cursor_labels = conn.execute("""
            SELECT do.label
            FROM detection_objects do
            JOIN prediction_sessions ps ON do.prediction_uid = ps.uid
            WHERE ps.timestamp >= datetime('now', '-7 days')
        """)
        all_labels = [row[0] for row in cursor_labels]
        label_counts = Counter(all_labels)

    return {
        "total_predictions": total_predictions,
        "average_confidence_score": avg_score,
        "most_common_labels":dict(label_counts.most_common(3))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
