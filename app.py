import os
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

import chainlit as cl
from chainlit.input_widget import Slider

try:
    import google.generativeai as genai
    from ingest import (
        setUpGoogleAPI,
        loadVectorDataBase,
        ingest_document,
        config,
    )

    print("✅ All imports successful")
except Exception as e:
    print(f"❌ Import error: {e}")
    traceback.print_exc()
    sys.exit(1)


# --- RAG Functions ---
def get_relevant_passages(query, db, n_results=10):
    """Retrieve relevant text passages from the vector database."""
    try:
        results = db.query(query_texts=[query], n_results=n_results)
        passages = results["documents"][0] if results["documents"] else []
        return passages
    except Exception as e:
        print(f"Error retrieving passages: {e}")
        return []


def make_prompt(query, relevant_passages):
    """Create a prompt combining the user query with relevant context."""
    context = "\n\n".join(relevant_passages) if relevant_passages else ""
    escaped = context.replace("'", "").replace('"', "").replace("\n", " ")

    if not context.strip():
        return f"""
Question: {query}

I don't have any relevant context to answer this question. Please upload a document first.

Your answer:
"""
    else:
        return f"""
Question: {query}

Context:
{escaped}

Instructions: Answer the question based on the provided context. If the question is not related to the context, respond with 'OUT OF CONTEXT'. Be concise and accurate.

Your answer:
"""


# --- Display uploaded files ---
async def display_uploaded_files():
    """Reload the persistent DB and list all uploaded files."""
    try:
        db = loadVectorDataBase()  # reconnect to persistent ChromaDB
        collection_data = db.get(include=["metadatas"])

        files = set()
        for metadata in collection_data.get("metadatas", []):
            if metadata and isinstance(metadata.get("source"), str):
                files.add(os.path.basename(metadata["source"]))

        if not files:
            await cl.Message(content="📁 No files found in the knowledge base.").send()
        else:
            files_list = "\n".join([f"📄 {file}" for file in sorted(files)])
            await cl.Message(
                content=f"**📚 Files in your knowledge base:**\n\n{files_list}"
            ).send()
    except Exception as e:
        print(f"Error displaying files: {e}")
        await cl.Message(content="❌ Error while listing files.").send()


# --- Chat Start ---
@cl.on_chat_start
async def start_chat():
    """Initialize the chat session with database and model setup."""
    await cl.Message(
        content="""
### **Welcome to Your Personalized RAG Assistant**
Hello! I'm your local RAG system. You can upload documents (PDF, TXT, MD), and I'll answer questions based on them.

**Features:**
1. 📎 Upload PDF, TXT, or Markdown documents.
2. ❓ Ask questions about your content.
3. ⚙️ Adjust model sliders for creativity and answer length.
4. 📚 Type `show files` to see uploaded documents.
5. 🔄 Type `reset settings` to restore defaults.

Note: Your vector database is stored locally. You can safely delete it to start fresh.
"""
    ).send()

    # Initialize Google API and DB
    setUpGoogleAPI()
    db = loadVectorDataBase()
    cl.user_session.set("db", db)
    cl.user_session.set("model", genai.GenerativeModel("gemini-1.5"))
    cl.user_session.set("config", config.copy())

    if db:
        await cl.Message(content="✅ Vector database loaded and ready!").send()
    else:
        await cl.Message(content="❌ Failed to load the vector database.").send()

    # Add sliders
    await cl.ChatSettings(
        [
            Slider(
                id="temperature",
                label="Temperature",
                initial=config["temperature"],
                min=0,
                max=1,
                step=0.01,
            ),
            Slider(
                id="top_p",
                label="Top P",
                initial=config["top_p"],
                min=0,
                max=1,
                step=0.01,
            ),
            Slider(
                id="top_k",
                label="Top K",
                initial=config["top_k"],
                min=1,
                max=50,
                step=1,
            ),
        ]
    ).send()


# --- Update settings ---
@cl.on_settings_update
async def setup_agent(settings):
    """Update generation configuration based on slider changes."""
    cl.user_session.set("gen_config_kwargs", settings)
    print(f"Settings updated: {settings}")
    await cl.Message(content="✅ Model settings updated!").send()


# --- Main message handler ---
@cl.on_message
async def main(message: cl.Message):
    """Handle user messages and file uploads."""

    # Handle file uploads
    if message.elements:
        for element in message.elements:
            if element.mime in ["application/pdf", "text/plain", "text/markdown"]:
                try:
                    file_path = element.path
                    db = cl.user_session.get("db")
                    if not db:
                        await cl.Message(
                            content="❌ Database not available. Restart session."
                        ).send()
                        return

                    await cl.Message(content=f"📄 Processing {element.name}...").send()
                    ingest_document(file_path, db)
                    await cl.Message(
                        content=f"✅ Document {element.name} ingested successfully!"
                    ).send()
                except Exception as e:
                    print(f"Error processing file: {e}")
                    await cl.Message(content="❌ Error processing the file.").send()
                return

    # Handle text commands
    user_input = message.content.lower().strip()

    if user_input in ["show files", "list files", "files"]:
        await display_uploaded_files()
        return

    if user_input in ["reset", "reset settings", "default settings"]:
        cl.user_session.set("gen_config_kwargs", {})
        cl.user_session.set("config", config.copy())
        await cl.Message(content="✅ Model settings reset to defaults.").send()
        return

    if user_input in ["help", "commands"]:
        await cl.Message(
            content="""🔧 **Commands:**

📚 File Management:
• `show files` - List uploaded documents
• Upload PDF/TXT/MD files using the attachment button

⚙️ Model Settings:
• `reset settings` - Reset sliders to default

❓ Ask questions about uploaded documents.
"""
        ).send()
        return

    # Handle normal queries
    try:
        model = cl.user_session.get("model")
        db = cl.user_session.get("db")
        session_config = cl.user_session.get("config", config)

        if not model or not db:
            await cl.Message(content="❌ Not initialized. Refresh the page.").send()
            return

        passages = get_relevant_passages(message.content, db, n_results=5)
        prompt = make_prompt(message.content, passages)

        msg = cl.Message(content="")
        await msg.send()

        try:
            stream = model.generate_content(
                prompt, stream=True, generation_config=session_config
            )
            for part in stream:
                if part.text:
                    await msg.stream_token(part.text)

        except Exception as e:
            # Handle quota exceeded specifically
            if "quota" in str(e).lower():
                await cl.Message(
                    content="❌ Gemini API quota exceeded. This means you have reached the maximum number of requests allowed for your current plan. Please try again tomorrow or upgrade your plan."
                ).send()
            else:
                await cl.Message(content=f"❌ Error generating response: {e}").send()
            print(f"Error generating response: {e}")

    except Exception as e:
        print(f"Error in main handler: {e}")
        await cl.Message(content="❌ Unexpected error. Try again.").send()
