from flask import Flask, request, jsonify
from Services.pdf_service import OrderMakerService
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['pdf_file']

    if file.filename == '':
        return jsonify({'error': 'Empty file'}), 400

    logger.info(f"Received file: {file.filename}, Size: {file.content_length} bytes")

    # Log first few bytes of the file
    file.seek(0)  # Reset pointer
    first_bytes = file.read(5)
    logger.info(f"File Header (first 5 bytes): {first_bytes}")

    file.seek(0)  # Reset again before passing to processing function
    extracted_json = OrderMakerService.create_order(file)

    return jsonify(extracted_json)



@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "message": "App is running"}), 200

if __name__ == '__main__':
    app.run(debug=True)
