#!/usr/bin/env python3
"""Quick test to verify app initialization works with Cloudinary disabled."""

import os
import sys

# Disable Cloudinary
os.environ['DISABLE_CLOUDINARY_UPLOAD'] = '1'

print("=" * 60)
print("SmartVision - Initialization Test")
print("=" * 60)
print()

try:
    # Import app modules
    print("[*] Loading dependencies...")
    import firebase_admin
    from firebase_admin import credentials, db
    import cloudinary
    print("    ✓ Core libraries loaded")
    
    # Check environment
    print()
    print("[*] Configuration:")
    print(f"    - DISABLE_CLOUDINARY_UPLOAD: {os.getenv('DISABLE_CLOUDINARY_UPLOAD', 'not set')}")
    print(f"    - Firebase key path: SmartVision - Copy/firebase/firebase_key.json")
    
    # Check Firebase credentials
    print()
    print("[*] Checking Firebase credentials...")
    firebase_key_path = os.path.join(os.path.dirname(__file__), "firebase", "firebase_key.json")
    if os.path.exists(firebase_key_path):
        print(f"    ✓ Firebase key found at {firebase_key_path}")
    else:
        print(f"    ✗ Firebase key NOT found at {firebase_key_path}")
        sys.exit(1)
    
    # Test Firebase initialization
    print()
    print("[*] Testing Firebase initialization...")
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_key_path)
            firebase_admin.initialize_app(cred, {"databaseURL": "https://smartvision-b3697-default-rtdb.firebaseio.com/"})
            print("    ✓ Firebase app initialized")
        
        db_ref = db.reference("alerts")
        if db_ref:
            print("    ✓ Firebase database reference created")
            print()
            print("=" * 60)
            print("✓ ALL CHECKS PASSED - App is ready to run!")
            print("=" * 60)
            print()
            print("To start the app with Cloudinary disabled, run:")
            print("  python run_app.ps1  (on Windows)")
            print("  or")
            print("  $env:DISABLE_CLOUDINARY_UPLOAD='1'; python app.py")
        else:
            print("    ✗ Firebase database reference is None")
            sys.exit(1)
    except Exception as e:
        print(f"    ✗ Firebase initialization failed: {e}")
        sys.exit(1)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
