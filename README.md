# 💊 m3dswft: AI-Powered Prescription OCR

A desktop app that extracts text from prescription images and PDFs using OCR technology. Built with Electron + Python for offline processing.

## Features

- **Drag & drop** prescription images (PNG, JPG) or PDFs
- **OCR text extraction** with spell correction
- **Offline processing** - no data leaves your machine
- **Copy to clipboard** for easy transfer to other systems

## Installation

### Prerequisites
- Node.js 16+
- Python 3.8+

### Setup
```bash
git clone https://github.com/muskanf/medi_ocr
cd medi_ocr
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
npm install
npm start
```

## Usage

1. Launch the app with `npm start`
2. Upload a prescription image/PDF or drag & drop
3. Wait for OCR processing
4. Copy extracted text to clipboard

## Build

```bash
# Create distributable package
npm run package
```

Built with Electron, Python (PyTesseract), and spell correction