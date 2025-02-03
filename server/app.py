import numpy as np
import pytesseract
import requests
from PIL import Image, ImageEnhance
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import io
import cv2

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_BASE_URL = "https://rxnav.nlm.nih.gov/REST"

# Preprocess the image for better OCR
def preprocess_image(image):
    # Convert to grayscale
    gray_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

    # Apply thresholding to make the image binary
    _, thresh_image = cv2.threshold(gray_image, 150, 255, cv2.THRESH_BINARY)

    # Noise removal with median blur
    clean_image = cv2.medianBlur(thresh_image, 3)

    # Enhance the image (Optional)
    pil_image = Image.fromarray(clean_image)
    enhancer = ImageEnhance.Contrast(pil_image)
    enhanced_image = enhancer.enhance(2.0)  # Increase contrast
    
    return enhanced_image

@app.get("/")
async def root():
    """
    Root endpoint to check if the medicine server is active
    """
    return {"message": "Medicine Server is Active"}

@app.post("/scan-medicine")
async def scan_medicine(file: UploadFile = File(...)):
    """
    Scan medicine image and fetch details from API
    """
    # Save and process uploaded file
    contents = await file.read()
    
    # Convert to PIL Image for preprocessing
    image = Image.open(io.BytesIO(contents))
    
    # Preprocess image for better OCR
    processed_image = preprocess_image(image)
    
    # Extract text using Tesseract OCR
    text = pytesseract.image_to_string(processed_image).lower()
    
    # Find medication name
    try:
        # Search for medication
        search_response = requests.get(f"{API_BASE_URL}/drugs.json", 
                                       params={"name": text})
        drugs = search_response.json().get('drugGroup', {}).get('conceptGroup', [])
        
        if drugs and len(drugs) > 0:
            # Get first drug details
            drug_name = drugs[0].get('conceptProperties', [{}])[0].get('name', 'Unknown')
            
            # Fetch detailed drug information
            details_response = requests.get(f"{API_BASE_URL}/rxcui/{drug_name}/properties.json")
            details = details_response.json()
            
            return {
                "status": "success",
                "medicine": {
                    "name": details.get('properties', {}).get('name', 'Unknown'),
                    "rxcui": details.get('properties', {}).get('rxcui', 'N/A'),
                    "uses": "Consult healthcare professional for specific uses",
                    "dosage": "Varies by individual - consult doctor",
                    "precautions": "Always follow medical advice"
                }
            }
        
        return {
            "status": "not_found",
            "message": "Medicine not identified"
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
