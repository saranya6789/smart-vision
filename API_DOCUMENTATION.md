# SmartVision API Documentation

## Base URL
```
http://localhost:5000
```

---

## 🔐 Authentication

### Login
- **Endpoint**: `POST /`
- **Parameters**:
  - `username` (string): Default: `admin`
  - `password` (string): Default: `admin`
  - `mode` (string): `normal` or `smart`
- **Response**: Redirect to `/dashboard` or error
- **Example**:
```bash
curl -X POST http://localhost:5000/ \
  -d "username=admin&password=admin&mode=smart"
```

### Logout
- **Endpoint**: `GET /logout`
- **Auth**: Required
- **Response**: Redirect to login page

---

## 📊 Health & Monitoring (No Auth Required)

### Health Check
- **Endpoint**: `GET /api/health`
- **Response**: System health status
- **Example Response**:
```json
{
  "timestamp": "2026-05-17T13:45:30.123456",
  "firebase_initialized": true,
  "firebase_available": true,
  "camera_available": true,
  "models_loaded": true,
  "metrics": {
    "alerts_total": 42,
    "alerts_firebase": 40,
    "alerts_local": 2,
    "cloudinary_uploads": 35,
    "cloudinary_failures": 5,
    "firebase_errors": 0,
    "start_time": "2026-05-17T10:00:00.000000"
  }
}
```

### Get Metrics
- **Endpoint**: `GET /api/metrics`
- **Response**: Current app metrics (JSON)
- **Example Response**:
```json
{
  "alerts_total": 42,
  "alerts_firebase": 40,
  "alerts_local": 2,
  "cloudinary_uploads": 35,
  "cloudinary_failures": 5,
  "firebase_errors": 0,
  "start_time": "2026-05-17T10:00:00.000000"
}
```

### Get System Status
- **Endpoint**: `GET /api/status`
- **Auth**: Required
- **Response**: Detailed system status
- **Example Response**:
```json
{
  "system_health": { ... },
  "active_mode": "smart",
  "cloudinary_enabled": true,
  "time_sync_status": "synchronized"
}
```

---

## 🎬 Video & Dashboard (Auth Required)

### Get Dashboard
- **Endpoint**: `GET /dashboard`
- **Auth**: Required
- **Response**: HTML dashboard page

### Get Video Feed
- **Endpoint**: `GET /video_feed`
- **Auth**: Required
- **Mimetype**: `multipart/x-mixed-replace; boundary=frame`
- **Response**: Real-time MJPEG stream with detections overlaid

### Get Surveillance View
- **Endpoint**: `GET /surveillance`
- **Auth**: Required
- **Response**: HTML surveillance page

---

## 🚨 Alert Management

### Alert Structure (Firebase)
```json
{
  "name": "Person_1",
  "behavior": "Running",
  "timestamp": "20260517_134530",
  "image": "https://cloudinary.url/image.jpg",
  "local_path": "alerts_local/Person_1_20260517_134530.jpg"
}
```

### Weapon Alert Structure (Firebase)
```json
{
  "weapon": "Gun",
  "timestamp": "20260517_134530",
  "image": "https://cloudinary.url/image.jpg",
  "local_path": "weapons_local/Gun_20260517_134530.jpg"
}
```

---

## ⚙️ Configuration

### Environment Variables
```bash
DISABLE_CLOUDINARY_UPLOAD=0|1
ALERT_COOLDOWN=10
MAX_LOCAL_ALERTS=500
CLEANUP_INTERVAL=3600
```

### Feature Flags

#### Disable Cloudinary
```bash
export DISABLE_CLOUDINARY_UPLOAD=1
python app.py
```

#### Change Alert Cooldown
```bash
export ALERT_COOLDOWN=20
python app.py
```

---

## 📈 Detection Modes

### Normal Mode
- Weapon detection only
- Lower resource usage
- 24/7 monitoring suitable

### Smart Mode
- Face recognition
- Weapon detection
- Behavior analysis (loitering, running)
- Higher resource usage

---

## 🔄 Alert Flow

### Face Detection Alert
```
1. Face detected in frame
2. Embedding extracted & compared
3. Unknown face detected
4. Alert cooldown checked (10s default)
5. Image saved locally
6. Cloudinary upload attempted (if enabled)
7. Firebase push with alert data
8. Alert displayed on dashboard
```

### Weapon Detection Alert
```
1. Weapon detected in frame (confidence > 0.5)
2. Alert cooldown checked (10s default)
3. Image saved locally
4. Cloudinary upload attempted (if enabled)
5. Firebase push with alert data
6. Alert displayed on dashboard
```

### Behavior Detection Alert
```
1. Person tracked (pose estimation)
2. Behavior analyzed (loitering > 25s, speed > 8)
3. Alert cooldown checked (10s per person)
4. Image saved locally
5. Cloudinary upload attempted (if enabled)
6. Firebase push with alert data
7. Alert displayed on dashboard
```

---

## 🔧 Error Handling

### Clock Skew Error
```
Status: 400
Message: "Stale request - reported time is more than 1 hour ago"
Cause: System clock not synchronized
Fix: Run `w32tm /resync /force` as admin
```

### Firebase JWT Error
```
Status: 401
Message: "Invalid JWT: Token must be a short-lived token"
Cause: System clock skewed + Firebase token expired
Fix: Sync system clock; app auto-retries
```

### Cloudinary Upload Error
```
Status: 400
Message: Various upload errors
Fallback: Stores alert locally; Firebase push still works
```

### Firebase Initialization Error
```
Status: 500
Message: "Firebase not initialized"
Cause: Invalid credentials or Firebase key path
Fix: Check firebase_key.json path and permissions
```

---

## 📡 Dashboard Real-time Updates

### Firebase Listeners
```javascript
// Dashboard listens to:
database.ref("alerts").on("value", ...)
database.ref("weapon_alerts").on("value", ...)

// Updates automatically when new alerts arrive
```

### Alert Deduplication
- Same alert type within cooldown period
- Prevents duplicate entries on dashboard
- Cooldown per person/weapon type

---

## 🎯 Monitoring Examples

### Check if app is running
```bash
curl http://localhost:5000/api/health
```

### Get total alerts count
```bash
curl http://localhost:5000/api/metrics | jq .alerts_total
```

### Monitor Cloudinary failures
```bash
curl http://localhost:5000/api/metrics | jq .cloudinary_failures
```

### Check camera status
```bash
curl http://localhost:5000/api/health | jq .metrics.camera_available
```

---

## 🚀 Integration Examples

### Save Alerts to External DB
```python
import requests

health = requests.get("http://localhost:5000/api/health").json()
metrics = requests.get("http://localhost:5000/api/metrics").json()

# Store in your database
save_to_db(health, metrics)
```

### Trigger Webhook on Alert
```python
# Modify upload_alert() to call:
requests.post("https://your-server.com/webhook", json=alert_data)
```

### Generate Reports
```python
metrics = requests.get("http://localhost:5000/api/metrics").json()
generate_pdf_report(metrics)
```

---

## 📊 Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 302 | Redirect (login required) |
| 400 | Bad request |
| 401 | Unauthorized (login required) |
| 404 | Not found |
| 500 | Server error |

---

## 🔒 Security Considerations

1. **Authentication**: Simple username/password (admin/admin)
   - Change in production!
   - Use proper auth (OAuth2, JWT, etc.)

2. **HTTPS**: Use reverse proxy (nginx, Apache) in production
   - Encrypt traffic
   - SSL certificates required

3. **Access Control**: Restrict to private network
   - Use firewall rules
   - VPN for remote access

4. **Rate Limiting**: Not implemented
   - Add if exposing publicly
   - Prevent abuse

---

## 📝 Logging

All events logged to `logs/smartvision_YYYYMMDD.log`

```
[2026-05-17T13:45:30.123456] ALERT_FIREBASE: Unknown / Unknown Face
[2026-05-17T13:45:31.654321] ALERT_LOCAL_ONLY: After cleanup
[2026-05-17T13:45:45.789012] CLEANUP: alerts_firebase=40 alerts_local=2
```

---

## 📚 Additional Resources

- Setup Guide: `SETUP_GUIDE.md`
- Troubleshooting: `FIX_GUIDE.md`
- Fixes & Improvements: `README_FIXES.md`
- Configuration Template: `config.env.example`

---

**Last Updated**: May 17, 2026
