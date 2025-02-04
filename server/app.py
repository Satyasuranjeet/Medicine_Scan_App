import os
import logging
import tempfile
import requests
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# OCR.Space API credentials
OCR_SPACE_API_KEY = 'K82241976688957'  # Replace with your OCR.Space API key

def parse_ocr_response(ocr_response):
    """Parse OCR response and extract medicine information."""
    try:
        # Check if response contains ParsedResults
        if not isinstance(ocr_response, dict) or 'ParsedResults' not in ocr_response:
            raise ValueError("Invalid OCR response format")

        parsed_results = ocr_response['ParsedResults']
        if not parsed_results or not isinstance(parsed_results[0], dict):
            raise ValueError("No parsed results found")

        # Extract text from ParsedResults
        if 'ParsedText' in parsed_results[0]:
            return parsed_results[0]['ParsedText']
        
        # Fallback to TextOverlay if ParsedText is not available
        if 'TextOverlay' in parsed_results[0]:
            lines = parsed_results[0]['TextOverlay'].get('Lines', [])
            return ' '.join(line.get('LineText', '') for line in lines)
            
        raise ValueError("No text content found in OCR response")
        
    except Exception as e:
        logger.error(f"Error parsing OCR response: {str(e)}")
        raise

def extract_medicine_info(text):
    """Extract medicine name and details from OCR text."""
    try:
        lines = text.split('\n')
        medicine_info = {
            'name': '',
            'composition': [],
            'dosage': '',
            'manufacturer': '',
            'batch_no': '',
            'mfg_date': '',
            'expiry_date': ''
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('Rx '):
                medicine_info['name'] = line.replace('Rx ', '')
            elif 'mg' in line and ':' not in line and 'Contains' not in line:
                medicine_info['composition'].append(line.strip())
            elif line.startswith('Dosage:'):
                medicine_info['dosage'] = line.replace('Dosage:', '').strip()
            elif 'LABORATORIES' in line or 'LTD.' in line:
                medicine_info['manufacturer'] = line.strip()
            elif line.startswith('Batch No.'):
                next_idx = lines.index(line) + 1
                if next_idx < len(lines):
                    medicine_info['batch_no'] = lines[next_idx].strip()
            elif 'Mfg. Date' in line:
                next_idx = lines.index(line) + 1
                if next_idx < len(lines):
                    medicine_info['mfg_date'] = lines[next_idx].strip()
            elif 'Expiry Date' in line:
                next_idx = lines.index(line) + 1
                if next_idx < len(lines):
                    medicine_info['expiry_date'] = lines[next_idx].strip()
        
        return medicine_info
    except Exception as e:
        logger.error(f"Error extracting medicine info: {str(e)}")
        raise

@app.route("/scan-medicine", methods=["POST"])
def scan_medicine():
    try:
        # Check if a file was uploaded
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file uploaded"})

        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No selected file"})

        # Save the uploaded image temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name

        try:
            # Call OCR.Space API
            with open(temp_path, 'rb') as image_file:
                payload = {
                    'apikey': OCR_SPACE_API_KEY,
                    'language': 'eng',
                    'isOverlayRequired': True,
                    'detectOrientation': True,
                    'scale': True,
                    'OCREngine': 2  # Using more accurate OCR engine
                }
                files = {'file': image_file}
                
                response = requests.post(
                    'https://api.ocr.space/parse/image',
                    files=files,
                    data=payload
                )
                response.raise_for_status()
                ocr_response = response.json()

            # Process OCR response
            if 'ErrorMessage' in ocr_response and ocr_response['ErrorMessage']:
                return jsonify({
                    "status": "error",
                    "message": f"OCR API Error: {ocr_response['ErrorMessage']}"
                })

            # Extract text from OCR response
            extracted_text = parse_ocr_response(ocr_response)
            if not extracted_text:
                return jsonify({
                    "status": "error",
                    "message": "No text could be extracted from the image"
                })

            # Extract medicine information
            medicine_info = extract_medicine_info(extracted_text)
            
            return jsonify({
                "status": "success",
                "medicine": medicine_info
            })

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Error deleting temporary file: {str(e)}")

    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "message": f"Error communicating with OCR service: {str(e)}"
        })
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}"
        })

if __name__ == "__main__":
    app.run(debug=True)