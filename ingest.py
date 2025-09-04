import os
from dotenv import load_dotenv
from typing import List

try:
    import PyPDF2

    print("✅ PyPDF2 imported successfully")
except ImportError as e:
    print(f"❌ PyPDF2 import failed: {e}")

try:
    import chromadb
    from chromadb import Documents, EmbeddingFunction, Embeddings

    print("✅ ChromaDB imported successfully")
except ImportError as e:
    print(f"❌ ChromaDB import failed: {e}")

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    print("✅ LangChain imported successfully")
except ImportError as e:
    print(f"❌ LangChain import failed: {e}")

    # Fallback text splitter
    class RecursiveCharacterTextSplitter:
        def __init__(
            self,
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=None,
        ):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.length_function = length_function
            self.separators = separators or ["\n\n", "\n", " ", ""]

        def split_text(self, text):
            if not text:
                return []
            # Simple splitting logic
            chunks = []
            current_chunk = ""
            sentences = text.split(". ")

            for sentence in sentences:
                if len(current_chunk + sentence) < self.chunk_size:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "

            if current_chunk:
                chunks.append(current_chunk.strip())

            return chunks


try:
    import google.generativeai as genai

    print("✅ Google GenerativeAI imported successfully")
except ImportError as e:
    print(f"❌ Google GenerativeAI import failed: {e}")

# This config dictionary is now shared across the project
config = {"max_output_tokens": 128, "temperature": 0.9, "top_p": 0.9, "top_k": 1}


# --- Shared Setup Functions ---
def setUpGoogleAPI():
    """Configures the Gemini API using an environment variable."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)


def loadVectorDataBase():
    """Loads or creates the ChromaDB collection."""
    # Use relative path to make it more portable
    db_path = os.path.join(os.getcwd(), "database")

    # Create database directory if it doesn't exist
    os.makedirs(db_path, exist_ok=True)

    chroma_client = chromadb.PersistentClient(path=db_path)

    db = chroma_client.get_or_create_collection(
        name="sme_db", embedding_function=GeminiEmbeddingFunction()
    )
    return db


# --- Embedding Function ---
class GeminiEmbeddingFunction(EmbeddingFunction):
    """Custom embedding function for ChromaDB using the Gemini API."""

    def __call__(self, input: Documents) -> Embeddings:
        try:
            model = "models/embedding-001"
            # Handle both single strings and lists of strings
            if isinstance(input, str):
                input = [input]

            embeddings = []
            for text in input:
                result = genai.embed_content(
                    model=model, content=text, task_type="retrieval_document"
                )
                embeddings.append(result["embedding"])

            return embeddings
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            # Return zero embeddings as fallback
            return [[0.0] * 768 for _ in input]  # 768 is typical embedding dimension


# --- Document Loading and Chunking ---
def load_and_chunk_pdf(file_path):
    """Loads a PDF and splits it into text chunks."""
    try:
        text = ""
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:  # Only add non-empty text
                    text += page_text + "\n"

        if not text.strip():
            print("No text extracted from PDF")
            return []

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = text_splitter.split_text(text)

        # Filter out very short chunks
        chunks = [chunk for chunk in chunks if len(chunk.strip()) > 50]

        return chunks

    except Exception as e:
        print(f"Error loading PDF {file_path}: {e}")
        return []


def ingest_document(file_path, db_collection):
    """Ingests a PDF document into the vector database."""
    try:
        print(f"Ingesting {file_path}...")
        chunks = load_and_chunk_pdf(file_path)

        if not chunks:
            print("No text found in PDF or chunks are too small.")
            return False

        # Create unique IDs and metadata
        base_name = os.path.basename(file_path)
        ids = [
            f"id{i}_{base_name}_{hash(chunk) % 10000}" for i, chunk in enumerate(chunks)
        ]
        metadatas = [
            {"source": file_path, "chunk_index": i} for i in range(len(chunks))
        ]

        db_collection.add(documents=chunks, ids=ids, metadatas=metadatas)

        print(f"Successfully ingested {len(chunks)} chunks from {base_name}.")
        return True

    except Exception as e:
        print(f"Error ingesting document {file_path}: {e}")
        return False
