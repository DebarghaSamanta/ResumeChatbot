from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.llms.base import LLM
from dotenv import load_dotenv
import pdfplumber, os
import google.generativeai as genai

# ===== Load environment variables =====
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
print("Gemini API Key Loaded:", api_key)

# ===== Configure Gemini =====
genai.configure(api_key=api_key)

# ===== FastAPI setup =====
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== FAISS persistence path =====
FAISS_INDEX_PATH = "resume_index"

# ===== Embeddings model =====
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# ===== Load FAISS if exists =====
if os.path.exists(FAISS_INDEX_PATH):
    vector_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
else:
    vector_store = None

# ===== Gemini LLM Wrapper =====
class GeminiLLM(LLM):
    @property
    def _llm_type(self):
        return "gemini"

    def _call(self, prompt: str, stop=None):
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")  # Free tier model
            response = model.generate_content(prompt,generation_config={"max_output_tokens": 500})
            return response.text
        except Exception as e:
            return f"Gemini API call failed: {e}"

    @property
    def _identifying_params(self):
        return {}

llm = GeminiLLM()

# ===== Upload Resume Endpoint =====
@app.post("/upload_resume/")
async def upload_resume(file: UploadFile = File(...)):
    global vector_store
    text = ""

    if file.filename.endswith(".pdf"):
        with pdfplumber.open(file.file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    else:
        text = (await file.read()).decode("utf-8")

    if vector_store is None:
        vector_store = FAISS.from_texts([text], embeddings)
    else:
        vector_store.add_texts([text])

    vector_store.save_local(FAISS_INDEX_PATH)
    return {"message": "Resume indexed successfully"}

# ===== Chat Endpoint =====
class ChatRequest(BaseModel):
    query: str

@app.post("/chat/")
async def chat(body: ChatRequest):
    global vector_store

    if not vector_store:
        return {"title": "Error", "suggestions": ["Please upload a resume first."]}

    query = body.query
    retriever = vector_store.as_retriever()

    prompt_template = """You are an AI Career Guide.  
Given the candidate's resume, answer the user query.  

**Rules:**
- Limit the answer to 10 bullet points (max 300 words).
- Prioritize the most impactful changes only.
- Return output in bullet points, separated by '||' for each point.

Context: {context}
Question: {question}"""
    PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": PROMPT}
    )

    raw_result = chain.run(query)

    # Split answer into bullet points by '||'
    suggestions = [s.strip("-• ") for s in raw_result.split("||") if s.strip()]

    return {
        "title": "AI Suggestions",
        "suggestions": suggestions
    }
