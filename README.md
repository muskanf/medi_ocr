# 💊 Prescription Ocr: AI-Powered Prescription Reader

**Prescription Ocr** is a lightweight, AI-powered desktop tool that lets pharmacists drag-and-drop prescription images or PDFs and automatically extracts structured medication information using state-of-the-art handwriting OCR.

Built with **Electron + Python**, it supports both **modern typed prescriptions** and **scanned handwritten faxes**.

---

## 🚀 Features

- 📄 Drag & drop or upload **PDFs / JPEGs / PNGs**
- 🧾 Extracts:
  - Patient name
  - Date of birth
  - Prescriber (doctor) name
  - Medication names, dosages, and sig (instructions)
- 📤 Outputs a structured JSON-like preview and lets you **"Send to RxConnect"**
- 💻 Works **offline**, runs locally (no data leaves your machine)

---

## 🖥 Demo

https://user-images.githubusercontent.com/yourvideo.gif  
📽 _Coming soon: full walkthrough GIF_

---

## 📦 Tech Stack

| Layer        | Tech Used                                     |
|-------------|------------------------------------------------|
| Frontend    | [Electron](https://www.electronjs.org/), HTML, JS |

---

## 🛠 Installation

### ✅ Prerequisites

- Node.js
- Python

---

### 🔧 Clone + Setup

```bash
git clone https://github.com/muskanf/prescription_ocr
cd prescription_ocr
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install
npm start
