import pdfplumber, logging, json, os
from utilities.openai_client import OpenAiClient
from langchain.text_splitter import RecursiveCharacterTextSplitter
from llama_index.core import ServiceContext, VectorStoreIndex, SimpleDirectoryReader, Document
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.core.text_splitter import TokenTextSplitter
from llama_index.core.query_engine import RetrieverQueryEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrderMakerService:
    openai_client = OpenAiClient()

    @staticmethod
    def create_order(pdf_path):
        """Creates an initial order from a PDF file and saves response as JSON."""
        pdf = pdfplumber.open(pdf_path)
        order_text = OrderMakerService.extract_text_from_pdf(pdf)
        logger.info(order_text)

        retriever = OrderMakerService.chunk_and_index_prompt(order_text)  
        prompt_data = retriever

        logger.info(prompt_data)
        prompt = OrderMakerService.full_prompt_creator(prompt_data)

        response = OrderMakerService.openai_client.chat(prompt)
        response_text = str(response).strip()
        response_text = response_text.replace("```json", "").replace("```", "").strip()

        json_path = pdf_path.replace(".pdf", ".json")

        try:
            json_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: {e}")
            logger.error(f"Raw response:\n{response_text}")
            return {"error": "Invalid JSON response from OpenAI", "raw_response": response_text}

        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)

        return {
            "filename": os.path.basename(pdf_path),
            "json_file": os.path.basename(json_path),
            "message": "File processed successfully"
        }

    @staticmethod
    def extract_text_from_pdf(pdf):
        """Extracts all text from a given PDF file."""
        text = ""
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

        return text.strip() if text else "No text found"

    @staticmethod
    def chunk_and_index_prompt(order_text, chunk_size=2048, overlap=0):
        """Dzieli tekst na chunki o rozmiarze 2048 tokenów i zwraca tylko pierwszy chunk."""
        text_splitter = TokenTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        chunks = text_splitter.split_text(order_text)

        if not chunks:
            return "No relevant data found"

        return chunks[0]

    
    @staticmethod
    def query_index(retriever, query):
        """Queries the indexed data using the retriever and returns relevant results."""
        query_engine = RetrieverQueryEngine(retriever=retriever)
        response = query_engine.query(query)
        response_text = "".join([node.text for node in reversed(response.source_nodes)])

        return response_text

    @staticmethod
    def full_prompt_creator(prompt):
        prefix = f"""
        You are a helpful assistant to a freight forwading company that analyzes the order
        data and returns the following information from it in polish:
        - company name, street name, country code, postal code and the city name at the unloading/unloading place
        - what type of cargo is being loaded, it's weight, quantity, whether there's pallete exchange or those are ADR goods (which type if co)
        - type of truck needed (assume standard/tautliner if not mentioned)
        - any additional information, references for loading/unloading
        - information about a company on the order, number of the order

        Here are the most relevant parts of the order:
        """
        suffix = f"""
        Format the response strictly as a JSON object. Do not include any explanations, additional text, or comments. The JSON response must follow this structure:

        ```json
        {{
            "numer_zlecenia": "123456",
            "data_zlecenia": "2025-03-01",
            "zleceniodawca": {{
                "nazwa": "Firma XYZ",
                "kod_kraju": "PL",
                "miasto": "Warszawa",
                "ulica": "ul. Przykładowa 10",
                "NIP": "1234567890",
                "email": "kontakt@firmaxyz.pl"
            }},
            "zaladunek": {{
                "data": "2025-03-05",
                "czas": "08:00-10:00",
                "firma_zaladunku": "Firma A",
                "kod_kraju": "DE",
                "miasto": "Berlin",
                "ulica_zaladunku": "Hauptstraße 5",
                "informacje": "Brak wymiany palet"
            }},
            "rozladunek": {{
                "data": "2025-03-06",
                "czas": "12:00-14:00",
                "firma_rozladunku": "Firma B",
                "kod_kraju": "FR",
                "miasto": "Paryż",
                "ulica_rozladunku": "Rue de Transport 20",
                "informacje": "Potrzebna rampa"
            }},
            "ladunek": {{
                "rodzaj": "Palety z elektroniką",
                "waga": "15",
                "ilosc": "10",
                "ADR": "Brak"
            }},
            "fracht": "1200 EUR",
            "termin": "30 dni",
            "Auto": "Standard/Tautliner"
        }}
        ```
        """

        return f"{prefix}\n{prompt}\n{suffix}"

