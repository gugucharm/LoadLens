from flask import Flask, request, jsonify
import os
from Services.pdf_service import OrderMakerService

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['pdf_file']
    
    if file.filename == '':
        return jsonify({'error': 'Empty file'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    extracted_text = OrderMakerService.create_order(file_path)
    json_file_path = file_path.replace(".pdf", ".json")

    return jsonify({
        "message": "File processed successfully",
        "filename": file.filename,
        "json_file": json_file_path
    })


if __name__ == '__main__':
    app.run(debug=True)
