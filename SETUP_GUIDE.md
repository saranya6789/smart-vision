# SmartVision - Complete Setup & Production Guide

## 📋 System Requirements

### Hardware
- Minimum: CPU with 4 cores, 8GB RAM
- Recommended: CPU with 6+ cores, 16GB RAM
- Storage: 10GB free (for models + local alerts cache)
- Camera: USB/built-in webcam

### Software
- Windows 10/11 or Linux
- Python 3.8+
- Git (optional, for version control)

---

## 🚀 Installation Steps

### 1. Install Python 3.8+ (if not already installed)
```powershell
# Verify Python installation
python --version
pip --version
```

### 2. Create Virtual Environment (Recommended)
```powershell
# Navigate to project directory
cd "SmartVision - Copy"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\Activate.ps1

# On Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies
```powershell
# Install required packages
pip install -r requirements.txt

# Or manually install key packages:
pip install flask opencv-python deepface ultralytics firebase-admin cloudinary numpy scikit-learn
```

### 4. Download Pre-trained Models
```powershell
# Models should be in these locations:
# - yolov8n-pose.pt (in project root)
# - yolov8n.pt (in project root)
# - weapon_detection/detect/smart_vision_v12/weights/best.pt

# The app will download them automatically on first run if missing
```

### 5. Download Known Faces
- Create folder: `Known_Faces/`
- Add subdirectories for each person: `Known_Faces/person_name/`
- Add JPG images of each person

### 6. Firebase Setup
- Download Firebase credentials
- Save as: `firebase/firebase_key.json`

### 7. System Clock Sync (CRITICAL!)
```powershell
# Open PowerShell as Administrator
w32tm /resync /force

# Verify:
Get-Date
w32tm /query /status
```

---

## ⚙️ Configuration

### Option 1: Environment Variables
```powershell
$env:DISABLE_CLOUDINARY_UPLOAD = "1"
$env:ALERT_COOLDOWN = "10"
python app.py
```

### Option 2: Copy config.env.example
```powershell
# Copy and customize
Copy-Item config.env.example config.env
# Edit config.env with your values
```

---

## 🎯 Running the App

### With Cloudinary Enabled (Full Features)
```powershell
# Make sure system clock is synced first!
python app.py
```

### With Cloudinary Disabled (Workaround)
```powershell
# Use this if Cloudinary keeps failing
PowerShell -ExecutionPolicy Bypass -File run_app.ps1

# Or manually:
$env:DISABLE_CLOUDINARY_UPLOAD = "1"
python app.py
```

### Via Startup Script (Recommended)
```powershell
PowerShell -ExecutionPolicy Bypass -File run_app.ps1
```

---

## 📊 Available Endpoints

### Public (No Authentication)
- `http://localhost:5000/` - Login page
- `http://localhost:5000/api/health` - System health check
- `http://localhost:5000/api/metrics` - App metrics

### Protected (Requires Login)
- `http://localhost:5000/dashboard` - Main dashboard
- `http://localhost:5000/surveillance` - Surveillance view
- `http://localhost:5000/video_feed` - Live video stream
- `http://localhost:5000/api/status` - Detailed status

---

## 🔍 Monitoring & Troubleshooting

### Check System Health
```
curl http://localhost:5000/api/health
```

### View Logs
```powershell
# Logs are saved in: logs/smartvision_YYYYMMDD.log
Get-Content logs/smartvision_*.log
```

### View Metrics
```
curl http://localhost:5000/api/metrics
```

### Common Issues & Fixes

| Issue | Cause | Solution |
|-------|-------|----------|
| Cloudinary stale request | System clock out of sync | Run `w32tm /resync /force` as admin |
| Firebase JWT error | System clock out of sync | Fix system clock |
| Camera not detected | No camera device | Check camera hardware/drivers |
| Model loading fails | Missing model files | App downloads automatically; check disk space |
| Memory errors | Insufficient RAM | Close unnecessary applications |

---

## 📁 Project Structure

```
SmartVision - Copy/
├── app.py                           # Main Flask application
├── config.env.example               # Configuration template
├── requirements.txt        # Python dependencies
├── run_app.ps1                      # Startup script
├── test_init.py                     # Initialization test
├── FIX_GUIDE.md                     # Troubleshooting guide
├── README_FIXES.md                  # Fixes & improvements guide
│
├── firebase/
│   └── firebase_key.json            # Firebase credentials (keep secret!)
│
├── Known_Faces/                     # Known face images
│   ├── person1/
│   └── person2/
│
├── weapon_detection/                # Weapon detection models
│   └── detect/
│       └── smart_vision_v12/
│           └── weights/
│               └── best.pt
│
├── templates/                       # HTML templates
│   ├── login.html
│   ├── dashboard.html
│   └── surveillance.html
│
├── alerts_local/                    # Local alert cache (auto-created)
├── weapons_local/                   # Local weapon alerts (auto-created)
├── logs/                            # Application logs (auto-created)
│
├── yolov8n-pose.pt                  # Pose detection model
├── yolov8n.pt                       # Object detection model
└── snapshots/                       # Temporary snapshots
```

---

## 🔐 Security Notes

1. **Never commit credentials to git**
   - Add `firebase_key.json` to `.gitignore`
   - Use environment variables for secrets

2. **Change default credentials**
   - Update `app.secret_key` in production
   - Use strong Firebase rules

3. **Use HTTPS in production**
   - nginx/Apache as reverse proxy
   - SSL certificate (Let's Encrypt)

4. **Restrict access**
   - Change default password
   - Use VPN/private network
   - Enable firewall rules

---

## 📈 Performance Optimization

### Reduce CPU Usage
```python
# In app.py:
FRAME_SKIP = 10         # Increase to skip more frames
LOITERING_TIME = 60     # Increase detection threshold
```

### Reduce Memory
```python
MAX_LOCAL_ALERTS = 100  # Reduce cache size
CLEANUP_INTERVAL = 1800 # Clean more frequently
```

### Optimize Detection
- Use smaller YOLO model (yolov8s instead of yolov8n)
- Reduce frame resolution
- Disable unused detection modes

---

## 📱 Dashboard Features

### Real-time Detection
- Face recognition with confidence scores
- Weapon detection with alerts
- Behavior analysis (loitering, running)

### Alert Management
- View recent alerts with timestamps
- Filtered by alert type
- Image thumbnails (if Cloudinary enabled)

### Live Feed
- Real-time video streaming
- Detection overlays
- Mode switching (Normal/Smart)

---

## 🛠️ Development Mode

### Enable Debug Logging
```python
# In app.py, set:
FLASK_DEBUG = True
```

### Read Logs in Real-time
```powershell
Get-Content -Path logs/smartvision_*.log -Tail 20 -Wait
```

### Test Individual Components
```powershell
python test_init.py  # Test initialization
```

---

## ✅ Pre-Deployment Checklist

- [ ] System clock synchronized
- [ ] Python 3.8+ installed
- [ ] All dependencies installed
- [ ] Firebase credentials configured
- [ ] Camera detected and working
- [ ] Models downloaded
- [ ] Known faces added
- [ ] Cloudinary (or disabled) configured
- [ ] Tested health endpoint
- [ ] Tested dashboard login
- [ ] Tested alert generation
- [ ] Logs configured
- [ ] Security settings hardened

---

## 🚀 Production Deployment

### Using Gunicorn (Production Server)
```powershell
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker (Optional)
```powershell
# Dockerfile would be needed
docker build -t smartvision .
docker run -p 5000:5000 smartvision
```

### Monitoring with Systemd (Linux)
```bash
# Create /etc/systemd/system/smartvision.service
# See deployment guide for details
```

---

## 📞 Support

- Check `FIX_GUIDE.md` for common issues
- Check `README_FIXES.md` for implementation details
- Review logs in `logs/` directory
- Check API health: `http://localhost:5000/api/health`

---

## 📝 Version History

- **v1.0** - Initial release with fixes
  - Defensive Firebase initialization
  - Local storage fallback
  - Health check endpoints
  - Metrics tracking
  - Cleanup routines
  - Graceful shutdown

---

**Last Updated**: May 17, 2026
