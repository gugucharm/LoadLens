import pdfplumber, logging, json, io, os
from utilities.openai_client import OpenAiClient
from llama_index.core.text_splitter import TokenTextSplitter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrderMakerService:
    openai_client = OpenAiClient()

    @staticmethod
    def create_order(pdf_file):
        """Processes a PDF file-like object and returns extracted JSON."""
        pdf_bytes = io.BytesIO(pdf_file.read())
        pdf_file.seek(0)

        if pdf_bytes.getbuffer().nbytes == 0:
            return {"error": "Uploaded file is empty or unreadable"}

        pdf_bytes.seek(0)
        header = pdf_bytes.read(5)

        logger.info(f"File Header: {header}") 

        if header != b"%PDF-":
            logger.error("Uploaded file is not a valid PDF")
            return {"error": "Invalid file format. Please upload a valid PDF."}

        pdf_bytes.seek(0)

        try:
            with pdfplumber.open(pdf_bytes) as pdf:
                order_text = OrderMakerService.extract_text_from_pdf(pdf)
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return {"error": "Invalid PDF file", "details": str(e)}
        
        if not order_text.strip():
            logger.error("Extracted text is empty!")
            return {"error": "No readable text found in the PDF."}

        logger.info(order_text)

        retriever = OrderMakerService.chunk_and_index_prompt(order_text)
        prompt_data = retriever

        logger.info(prompt_data)
        prompt = OrderMakerService.full_prompt_creator(prompt_data)

        response = OrderMakerService.openai_client.chat(prompt)
        response_text = str(response).strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()

        try:
            json_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e}")
            logger.error(f"Raw response:\n{response_text}")
            return {"error": "Invalid JSON response from OpenAI", "raw_response": response_text}
         
        output_path = os.path.join("orders", "order.json")
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Failed to save order.json: {e}")
            return {"error": "Failed to save output JSON", "details": str(e)}
        
        return json_data

    @staticmethod
    def extract_text_from_pdf(pdf):
        """Extracts all text from a given PDF file."""
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip() if text else "No text found"

    @staticmethod
    def chunk_and_index_prompt(order_text, chunk_size=2048, overlap=0):
        """Splits text into chunks and returns the first chunk."""
        text_splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        chunks = text_splitter.split_text(order_text)
        return chunks[0] if chunks else "No relevant data found"

    @staticmethod
    def full_prompt_creator(prompt):
        """Formats the extracted text into a structured prompt for OpenAI."""
        prefix = """
        You are a helpful assistant to a freight forwarding company that analyzes the order
        data and returns structured information in Polish. Extract the following details:
        - Company names, addresses, country codes for loading/unloading locations
        - Cargo type, weight, quantity, pallet exchange, ADR details (if applicable)
        - Truck type needed (assume standard tautliner if not specified)
        - Any additional loading/unloading references
        - Order details: company info, order number
        """
        suffix = """
        Format the response as a strict JSON object:
        ```json
        {
            "numer_zlecenia": "123456",
            "data_zlecenia": "2025-03-01",
            "zleceniodawca": {
                "nazwa": "Firma XYZ",
                "kod_kraju": "PL",
                "miasto": "Warszawa",
                "ulica": "ul. Przykładowa 10",
                "NIP": "1234567890",
                "email": "kontakt@firmaxyz.pl"
            },
            "zaladunek": {
                "data": "2025-03-05",
                "czas": "08:00-10:00",
                "firma_zaladunku": "Firma A",
                "kod_kraju": "DE",
                "miasto": "Berlin",
                "ulica_zaladunku": "Hauptstraße 5",
                "informacje": "Brak wymiany palet"
            },
            "rozladunek": {
                "data": "2025-03-06",
                "czas": "12:00-14:00",
                "firma_rozladunku": "Firma B",
                "kod_kraju": "FR",
                "miasto": "Paryż",
                "ulica_rozladunku": "Rue de Transport 20",
                "informacje": "Potrzebna rampa"
            },
            "ladunek": {
                "rodzaj": "Palety z elektroniką",
                "waga": "15",
                "ilosc": "10",
                "ADR": "Brak"
            },
            "fracht": "1200 EUR",
            "termin": "30 dni",
            "Auto": "Standard/Tautliner"
        }
        ```
        """

        return f"{prefix}\n{prompt}\n{suffix}"
