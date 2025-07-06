import os
import cv2
import numpy as np
import pytesseract

# --------- Image Processing Functions ---------

def enhance_image(img):
    denoised = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
    sharpen_kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]])
    sharpened = cv2.filter2D(denoised, -1, sharpen_kernel)

    lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    enhanced = cv2.merge((cl, a, b))
    final = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    return final

def detect_faces_and_text(img):
    img_copy = img.copy()
    gray = cv2.cvtColor(img_copy, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)

    text = pytesseract.image_to_string(img_copy)
    print("Detected text:", text.strip())
    return img_copy

def preprocess_for_model(img, target_size=(224, 224)):
    img = cv2.resize(img, target_size)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))  # HWC → CHW
    return img

# --------- Main Batch Processing ---------

def process_image_folder(input_folder, output_base):
    # Create subfolders
    enhanced_folder = os.path.join(output_base, "enhanced")
    annotated_folder = os.path.join(output_base, "annotated")
    preprocessed_folder = os.path.join(output_base, "preprocessed")
    os.makedirs(enhanced_folder, exist_ok=True)
    os.makedirs(annotated_folder, exist_ok=True)
    os.makedirs(preprocessed_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(('.jpg', '.png', '.jpeg')):
            path = os.path.join(input_folder, filename)
            img = cv2.imread(path)

            if img is None:
                continue

            # Step 1: Enhance image
            enhanced = enhance_image(img)
            cv2.imwrite(os.path.join(enhanced_folder, filename), enhanced)

            # Step 2: Annotate (face/text)
            annotated = detect_faces_and_text(enhanced)
            cv2.imwrite(os.path.join(annotated_folder, filename), annotated)

            # Step 3: Preprocess for model
            tensor = preprocess_for_model(enhanced)
            np.save(os.path.join(preprocessed_folder, filename.replace('.', '_') + ".npy"), tensor)

            print(f"Processed: {filename}")

    print("✅ All images processed and saved to separate folders.")

# --------- Run it ---------

if __name__ == "__main__":
    input_dir = "D:\Summer_2025\AIC\Data\L01_V001"             # Folder with your images
    output_dir = "processed_outputs"    # Base folder for outputs
    process_image_folder(input_dir, output_dir)
