import os
import requests
from flask import Flask, request, jsonify
from PIL import Image

app = Flask(__name__)

# API key for OCR.Space
OCR_API_KEY = 'K82241976688957'

# Function to process the image using OCR.Space API
def ocr_space_file(filename, overlay=False, api_key=OCR_API_KEY, language='eng'):
    """OCR.space API request with local file."""
    payload = {
        'isOverlayRequired': overlay,
        'apikey': api_key,
        'language': language,
    }
    with open(filename, 'rb') as f:
        r = requests.post('https://api.ocr.space/parse/image',
                          files={filename: f},
                          data=payload)
    return r.json()

@app.route("/")
def root():
    """Root endpoint to check if the medicine server is active."""
    return jsonify({"message": "Medicine Server is Active"})

@app.route("/scan-medicine", methods=["POST"])
def scan_medicine():
    """Scan medicine image and fetch details from API."""
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file part"})

        file = request.files['file']

        # If no file is selected
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"})

        # Save the uploaded image temporarily to process it
        filename = os.path.join("/tmp", file.filename)
        file.save(filename)

        # Use OCR.Space API to extract text from the image
        ocr_response = ocr_space_file(filename)

        # Extract the text result from the OCR response
        text = ""
        if ocr_response.get('OCRExitCode') == 1:
            # Extracting the OCR text result
            text = ' '.join([line['text'] for line in ocr_response.get('ParsedResults', [])[0].get('TextOverlay', {}).get('Lines', [])])

        # Clean the text (remove special characters)
        text = ''.join(e for e in text if e.isalnum() or e.isspace())

        # If no text is found, return an error message
        if not text:
            return jsonify({"status": "error", "message": "No text found in the image"})

        # Try to find medication using the extracted text
        search_response = requests.get(f"https://rxnav.nlm.nih.gov/REST/drugs.json", params={"name": text})

        # Check if the response is successful
        if search_response.status_code != 200:
            return jsonify({"status": "error", "message": "Failed to fetch drug data from API"})

        drugs = search_response.json().get('drugGroup', {}).get('conceptGroup', [])

        if drugs:
            # Get first drug details
            drug_name = drugs[0].get('conceptProperties', [{}])[0].get('name', 'Unknown')

            # Fetch detailed drug information
            details_response = requests.get(f"https://rxnav.nlm.nih.gov/REST/rxcui/{drug_name}/properties.json")

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
    port = int(os.environ.get("PORT", 5000))  # Use dynamic port if deployed
    app.run(host="0.0.0.0", port=port, debug=True)
