import os
import numpy as np
import pytesseract
import requests
from PIL import Image, ImageEnhance
import cv2
from flask import Flask, request, jsonify

app = Flask(__name__)

API_BASE_URL = "https://rxnav.nlm.nih.gov/REST"

# Preprocess the image for better OCR
def preprocess_image(image):
    # Convert to grayscale
    gray_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

    # Apply adaptive thresholding for better contrast
    thresh_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)

    # Noise removal with median blur
    clean_image = cv2.medianBlur(thresh_image, 3)

    # Enhance the image (Optional)
    pil_image = Image.fromarray(clean_image)
    enhancer = ImageEnhance.Contrast(pil_image)
    enhanced_image = enhancer.enhance(2.0)  # Increase contrast
    
    return enhanced_image

@app.route("/")
def root():
    """
    Root endpoint to check if the medicine server is active
    """
    return jsonify({"message": "Medicine Server is Active"})

@app.route("/scan-medicine", methods=["POST"])
def scan_medicine():
    """
    Scan medicine image and fetch details from API
    """
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file part"})
        
        file = request.files['file']

        # If no file is selected
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"})
        
        # Convert to PIL Image for preprocessing
        image = Image.open(file.stream)
        
        # Preprocess image for better OCR
        processed_image = preprocess_image(image)
        
        # Extract text using Tesseract OCR
        text = pytesseract.image_to_string(processed_image).lower().strip()
        
        # Clean the text if necessary (remove unwanted characters)
        text = ''.join(e for e in text if e.isalnum() or e.isspace())

        # If no text is found, return an error message
        if not text:
            return jsonify({"status": "error", "message": "No text found in the image"})

        # Try to find medication using the extracted text
        search_response = requests.get(f"{API_BASE_URL}/drugs.json", 
                                       params={"name": text})
        
        # Check if the response is successful
        if search_response.status_code != 200:
            return jsonify({"status": "error", "message": "Failed to fetch drug data from API"})
        
        drugs = search_response.json().get('drugGroup', {}).get('conceptGroup', [])
        
        if drugs:
            # Get first drug details
            drug_name = drugs[0].get('conceptProperties', [{}])[0].get('name', 'Unknown')
            
            # Fetch detailed drug information
            details_response = requests.get(f"{API_BASE_URL}/rxcui/{drug_name}/properties.json")
            
            # Check if the response is successful
            if details_response.status_code != 200:
                return jsonify({"status": "error", "message": "Failed to fetch drug details"})
            
            details = details_response.json()
            
            return jsonify({
                "status": "success",
                "medicine": {
                    "name": details.get('properties', {}).get('name', 'Unknown'),
                    "rxcui": details.get('properties', {}).get('rxcui', 'N/A'),
                    "uses": "Consult healthcare professional for specific uses",
                    "dosage": "Varies by individual - consult doctor",
                    "precautions": "Always follow medical advice"
                }
            })
        
        return jsonify({
            "status": "not_found",
            "message": "Medicine not identified"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Get port from environment variable
    app.run(debug=True, host="0.0.0.0", port=port)