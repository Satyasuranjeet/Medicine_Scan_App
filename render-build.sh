#!/bin/bash
# Update package lists
apt-get update

# Install Tesseract-OCR and required dependencies
apt-get install -y tesseract-ocr libtesseract-dev

# Install Python dependencies
pip install -r requirements.txt
