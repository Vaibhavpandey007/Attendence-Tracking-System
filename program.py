import cv2  
import numpy as np 
import csv  
import os
from datetime import datetime

# Load the Haar cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

video_capture = cv2.VideoCapture(0)


def load_reference_images():
    """Load and process reference images from Photos folder"""
    reference_images = {}
    reference_names = [
        'Bill Gates',
        'Linus Torvalds', 
        'Ratan Naval Tata',
        'Sundar Pichai',
        'Nikola Tesla',
        'Vaibhav Pandey'
    ]
    
    photo_files = ['Bill.png', 'linux.png', 'ratantata.png', 'pichai.png', 'tesla.png', 'Vaibhav.jpg']
    
    for i, photo_file in enumerate(photo_files):
        photo_path = f'Photos/{photo_file}'
        if os.path.exists(photo_path):
            img = cv2.imread(photo_path)
            if img is not None:
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(faces) > 0:
                    # Take the first detected face
                    x, y, w, h = faces[0]
                    face_roi = gray[y:y+h, x:x+w]
                    # Resize to standard size for better comparison
                    face_roi = cv2.resize(face_roi, (100, 100))
                    reference_images[reference_names[i]] = face_roi
                    print(f"✅ Loaded reference image for {reference_names[i]} from {photo_file}")
                else:
                    print(f"❌ No face found in {photo_file}")
            else:
                print(f"❌ Could not load image: {photo_path}")
        else:
            print(f"❌ Photo not found: {photo_path}")
    
    return reference_images


reference_images = load_reference_images()
known_face_names = list(reference_images.keys())


students = known_face_names.copy()
attendance_marked = set()  
current_person = None  

def recognize_face(face_roi):
    """Recognize face by comparing with reference images"""
    if len(reference_images) == 0:
        return 'Unknown'
    
    best_match = None
    best_score = float('inf')
    
    # Resize face_roi to standard size for comparison
    face_roi_resized = cv2.resize(face_roi, (100, 100))
    
    for name, ref_face in reference_images.items():
        # Reference face is already resized to 100x100
        # Calculate multiple similarity metrics
        diff = cv2.absdiff(face_roi_resized, ref_face)
        mean_diff = np.mean(diff)
        
        # Also calculate structural similarity
        # Normalize both images
        face_norm = cv2.normalize(face_roi_resized, None, 0, 255, cv2.NORM_MINMAX)
        ref_norm = cv2.normalize(ref_face, None, 0, 255, cv2.NORM_MINMAX)
        
        # Calculate correlation
        correlation = cv2.matchTemplate(face_norm, ref_norm, cv2.TM_CCOEFF_NORMED)[0][0]
        
        # Combined score (lower is better)
        combined_score = mean_diff - (correlation * 20)  # Correlation helps reduce false positives
        
        if combined_score < best_score:
            best_score = combined_score
            best_match = name
    
    # More strict threshold for better accuracy
    if best_score > 30:  # Reduced threshold for better accuracy
        return 'Unknown'
    
    return best_match

now = datetime.now()
current_date = now.strftime("%Y-%m-%d")
filename = current_date + '.csv'


file_exists = os.path.isfile(filename)

f = open(filename, 'a', newline='')  
inwriter = csv.writer(f)


if not file_exists:
    inwriter.writerow(["Name", "Date", "Time", "Status"])


attendance_complete = False
attendance_message_timer = 0

while True:
    ret, frame = video_capture.read()
    if not ret:
        print("ERROR")
        break

    if len(attendance_marked) >= len(known_face_names):
        if not attendance_complete:
            print("🎉 All attendance completed! Closing camera...")
            attendance_complete = True
            cv2.putText(frame, "All Attendance Complete!", 
                        (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
            cv2.imshow("Attendance System", frame)
            cv2.waitKey(3000)  # Wait 3 seconds before closing
            break


    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    

    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
   
    cv2.putText(frame, f"Students Present: {len(attendance_marked)}/{len(known_face_names)}", 
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
  
    remaining_students = [name for name in known_face_names if name not in attendance_marked]
    if remaining_students:
        cv2.putText(frame, f"Waiting for: {', '.join(remaining_students[:2])}", 
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    face_names = []
    for (x, y, w, h) in faces:
        
        face_roi = gray[y:y+h, x:x+w]
        
       
        name = recognize_face(face_roi)
        face_names.append(name)
        
        
        if name != "Unknown" and name in known_face_names:
            if name in attendance_marked:
                color = (0, 255, 255)  
                status = "Already Marked"
            else:
                color = (0, 255, 0)  
                status = "Recognized"
        else:
            color = (0, 0, 255)  
            status = "Unknown"
        
        
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        
        
        cv2.rectangle(frame, (x, y-50), (x+w, y), color, cv2.FILLED)
        cv2.putText(frame, name, (x + 6, y - 30),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, status, (x + 6, y - 10),
                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
        
        
        if name != "Unknown" and name in known_face_names and name not in attendance_marked:
            attendance_marked.add(name)
            current_time = datetime.now().strftime("%H:%M:%S")
            inwriter.writerow([name, current_date, current_time, "Present"])
            print(f"✅ Attendance marked for {name} at {current_time}")
            
            
            cv2.putText(frame, f"✅ ATTENDANCE MARKED: {name}", 
                        (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            attendance_message_timer = 30  # Show message for 30 frames

   
    if attendance_message_timer > 0:
        attendance_message_timer -= 1
        cv2.putText(frame, f"✅ ATTENDANCE MARKED: {name}", 
                    (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    
    cv2.imshow("Attendance System", frame)

   
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


video_capture.release()
cv2.destroyAllWindows()
f.close()


