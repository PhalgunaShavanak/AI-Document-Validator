import os
import re  # <-- Add this import for regular expressions
import pytesseract
import fitz  # PyMuPDF
import cv2
from flask import Flask, request, render_template, redirect, url_for

# Specify the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Extract text from image using OCR
def extract_text_from_image(image_path):
    text = pytesseract.image_to_string(cv2.imread(image_path))
    return text

# Extract relevant information using regex
def extract_info(text):
    # Debugging: Print the entire extracted text
    print("Extracted Text:\n", text)

    # Updated regex to account for potential variations in spacing and line breaks
    vendor_name = re.search(r'(?i)Vendor\s*Name:\s*(.*)', text)
    price = re.search(r'(?i)Price:\s*([0-9,.]+)', text)  # Assuming price is numeric
    gst_number = re.search(r'(?i)GST\s*Number:\s*([A-Z0-9]+)', text)
    address = re.search(r'(?i)Address:\s*(.*)', text)
    
    return {
        'vendor_name': vendor_name.group(1).strip() if vendor_name else None,
        'price': price.group(1).strip() if price else None,
        'gst_number': gst_number.group(1).strip() if gst_number else None,
        'address': address.group(1).strip() if address else None
    }

# Convert PDF to images and extract text
def convert_pdf_to_text(pdf_path):
    document = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        pix = page.get_pixmap()
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"page_{page_num}.png")
        pix.save(image_path)
        text += extract_text_from_image(image_path)
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        quotation_file = request.files['quotation_file']
        invoice_file = request.files['invoice_file']
        
        if quotation_file and invoice_file:
            quotation_path = os.path.join(app.config['UPLOAD_FOLDER'], quotation_file.filename)
            invoice_path = os.path.join(app.config['UPLOAD_FOLDER'], invoice_file.filename)
            
            quotation_file.save(quotation_path)
            invoice_file.save(invoice_path)
            
            quotation_text = convert_pdf_to_text(quotation_path)
            invoice_text = convert_pdf_to_text(invoice_path)
            
            # Debugging: Print the extracted text to check format
            print("Quotation Text:\n", quotation_text)
            print("Invoice Text:\n", invoice_text)
            
            quotation_info = extract_info(quotation_text)
            invoice_info = extract_info(invoice_text)
            
            # Compare information
            discrepancies = []
            for key in quotation_info.keys():
                if quotation_info[key] != invoice_info[key]:
                    discrepancies.append(key)
            
            return render_template('comparison_result.html', 
                                   quotation_info=quotation_info, 
                                   invoice_info=invoice_info, 
                                   discrepancies=discrepancies)
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
