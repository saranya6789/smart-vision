import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://smartvision-b3697-default-rtdb.firebaseio.com/"
})

ref = db.reference("test")
ref.set({
    "message": "Firebase connected successfully"
})

print("Data sent to Firebase successfully")