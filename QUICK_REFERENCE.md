# SmartVision - Quick Reference Card

## 🚀 START HERE

```powershell
# Option 1: Normal start
python app.py

# Option 2: With workarounds (if Cloudinary fails)
PowerShell -ExecutionPolicy Bypass -File run_app.ps1
```

**Access**: http://localhost:5000  
**Login**: `admin` / `admin`

---

## 📋 Essential Commands

```powershell
# Check if app is working
curl http://localhost:5000/api/health

# View metrics
curl http://localhost:5000/api/metrics

# View today's logs
Get-Content logs/smartvision_*.log

# Sync system clock (ADMIN REQUIRED)
w32tm /resync /force

# Install dependencies
pip install -r requirements.txt

# Test initialization
python test_init.py
```

---

## 🔧 Quick Fixes

| Problem | Solution |
|---------|----------|
| Cloudinary stale request | `w32tm /resync /force` (as admin) |
| Firebase JWT error | Fix system clock |
| Camera not detected | Check Device Manager in Settings |
| App won't start | Check `python --version` ≥ 3.8 |
| No alerts | Check `/api/health` endpoint |

---

## 📁 Important Directories

```
alerts_local/          ← Local alert backup storage
weapons_local/         ← Local weapon detection backup
logs/                  ← Application logs (read here for errors)
firebase/              ← Firebase credentials (KEEP SECRET!)
Known_Faces/           ← Add person folders with images
weapon_detection/      ← Weapon detection models
```

---

## 🌐 API Endpoints

**No Auth Required**:
```
/api/health            → System status
/api/metrics           → Usage statistics
/                      → Login page
```

**Auth Required**:
```
/dashboard             → Main dashboard
/video_feed            → Live stream
/surveillance          → Surveillance view
/api/status            → Detailed status
```

---

## ⚙️ Environment Variables

```powershell
# Disable Cloudinary
$env:DISABLE_CLOUDINARY_UPLOAD = "1"

# Change alert cooldown (seconds)
$env:ALERT_COOLDOWN = "20"

# Change local cache size
$env:MAX_LOCAL_ALERTS = "1000"

# Then start:
python app.py
```

---

## 📊 Key Metrics to Monitor

```javascript
alerts_total           // Total detections
alerts_firebase        // Successfully saved to database
alerts_local          // Saved locally (fallback)
cloudinary_uploads    // Successful cloud uploads
cloudinary_failures   // Upload failures
firebase_errors       // Database errors
```

**Check via**: `http://localhost:5000/api/metrics`

---

## 🎯 Detection Modes

**Normal Mode**: Weapon detection only (fast, 24/7 suitable)

**Smart Mode**: Face + Weapon + Behavior analysis (requires more compute)

*Select at login screen*

---

## ✅ System Health Indicators

**Green (✓ Working)**:
```
✓ Firebase database references created successfully
✓ Pose model loaded
✓ Weapon model loaded
✓ Camera opened successfully
```

**Red (✗ Problem)**:
```
✗ Firebase initialization failed
✗ Firebase not initialized
⚠️ System clock skew detected
✗ Camera not available
```

*Check app startup console*

---

## 🚨 Alert Types

| Type | Trigger | Actions |
|------|---------|---------|
| Unknown Face | Unknown person detected | Email, Log, Store |
| Weapon | Gun/Knife detected | Alert, Log, Store |
| Loitering | Person stays >25s | Alert, Log, Store |
| Running | Person speed >8 | Alert, Log, Store |

---

## 📈 Performance Tips

```python
# Reduce CPU (higher = faster but more load)
FRAME_SKIP = 10         # Skip more frames

# Reduce Memory
MAX_LOCAL_ALERTS = 100  # Smaller cache

# Faster alerts
ALERT_COOLDOWN = 5     # Shorter wait between alerts
```

*Edit config.env or set environment variables*

---

## 🔒 Security Reminders

- [ ] Change default password (admin/admin)
- [ ] Never share firebase_key.json
- [ ] Use HTTPS in production
- [ ] Restrict network access (firewall)
- [ ] Change Flask SECRET_KEY in production
- [ ] Keep logs secure (they contain timestamps/data)

---

## 📞 Troubleshooting Flowchart

```
App won't start?
├─ python --version ≥ 3.8? → NO → Install Python 3.8+
├─ pip install -r requirements.txt done? → NO → Do it now
└─ Firebase key exists? → NO → Download from Firebase Console

Alerts not working?
├─ /api/health returning OK? → NO → Check logs
├─ Camera detected? → NO → Check Device Manager
├─ Firebase initialized? → NO → Check firebase_key.json
└─ Check logs for errors

Cloudinary errors?
├─ Clock synchronized? → NO → w32tm /resync /force
├─ Try workaround → DISABLE_CLOUDINARY_UPLOAD=1
└─ Full feature requires fixed clock
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| README.md | Overview & feature introduction |
| SETUP_GUIDE.md | Installation & deployment |
| API_DOCUMENTATION.md | API endpoints & integration |
| FIX_GUIDE.md | Troubleshooting & solutions |
| IMPROVEMENTS_SUMMARY.md | What was improved |

---

## 🎬 Common Workflows

### Setup & First Run
```powershell
1. pip install -r requirements.txt
2. Create Known_Faces/person1/, Known_Faces/person2/, etc.
3. python app.py
4. localhost:5000 → Login (admin/admin) → Select mode
5. Allow camera access when prompted
```

### Debug & Troubleshoot
```powershell
1. Check /api/health endpoint
2. Read logs: Get-Content logs/smartvision_*.log
3. Check system clock: w32tm /query /status
4. Check Firebase credentials exist
5. Try workaround: $env:DISABLE_CLOUDINARY_UPLOAD="1"
```

### Production Deployment
```powershell
1. Review SETUP_GUIDE.md
2. Set up environment variables
3. Configure firewall/security
4. Use gunicorn or Docker
5. Monitor /api/health endpoint
6. Set up log rotation
```

---

## 🏃 Emergency Fixes (Try These First)

```powershell
# Fix 1: Sync clock (most common issue)
w32tm /resync /force

# Fix 2: Disable Cloudinary workaround
$env:DISABLE_CLOUDINARY_UPLOAD = "1"

# Fix 3: Restart app
# Stop current app (Ctrl+C), then:
python app.py

# Fix 4: Check logs
Get-Content logs/smartvision_*.log -Tail 100

# Fix 5: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 🎯 One-Liner Checklist

```powershell
# ✓ Python installed?
python --version

# ✓ Dependencies installed?
pip list | findstr flask

# ✓ Firebase key exists?
Test-Path firebase/firebase_key.json

# ✓ Clock synced?
w32tm /query /status | findstr synchronized

# ✓ App running?
curl http://localhost:5000/api/health

# ✓ System healthy?
(curl http://localhost:5000/api/health | ConvertFrom-Json).firebase_available
```

---

## 💡 Pro Tips

1. **Keep a terminal open** to watch logs while testing
2. **Use /api/health** as first diagnostic step
3. **System clock** is the #1 issue - check it first
4. **Local backup** means no data loss (Cloudinary optional)
5. **Environment vars** make testing easy without code changes
6. **Logs directory** contains all error details
7. **Disable Cloudinary** if you just want it working fast
8. **Monitor metrics** to understand system behavior

---

## 📞 When Everything Else Fails

```powershell
# 1. Stop the app (Ctrl+C)
# 2. Check logs for errors
Get-Content logs/smartvision_*.log -Tail 50

# 3. Verify Python
python --version

# 4. Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# 5. Check system clock
w32tm /query /status

# 6. If clock wrong, fix it:
w32tm /resync /force  # Needs admin!

# 7. Start with workaround
$env:DISABLE_CLOUDINARY_UPLOAD = "1"
python app.py

# 8. If still broken, read FIX_GUIDE.md
```

---

## 🎓 Key Concepts

**Modes**:
- Normal = Weapon detection only
- Smart = Face + Weapon + Behavior

**Alert Tiers**:
- Tier 1: Cloud (Cloudinary)
- Tier 2: Database (Firebase)
- Tier 3: Local storage (always works)

**Cooldown**: Prevents duplicate alerts (default 10s)

**Health Check**: `/api/health` tells you if system is working

---

## Quick Links

- **Start App**: `python app.py`
- **Dashboard**: http://localhost:5000
- **Health**: http://localhost:5000/api/health
- **Metrics**: http://localhost:5000/api/metrics
- **Logs**: `logs/smartvision_*.log`
- **Setup Guide**: `SETUP_GUIDE.md`
- **Troubleshooting**: `FIX_GUIDE.md`
- **Full Docs**: `README.md`

---

**SmartVision - Quick Reference Card**  
*Print this or save as bookmark for quick access*  
Last Updated: May 17, 2026
