from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from summarizer import summarize
import io
import pdfplumber
import docx2txt
import tempfile
import os
import torch
from typing import Optional

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def extract_text_from_pdf(file: UploadFile) -> str:
    """Extracts text from PDF with proper error handling and fallback"""
    try:
        # Read file content into memory
        contents = file.file.read()
        
        # Create a BytesIO object and open with pdfplumber
        with io.BytesIO(contents) as pdf_file:
            doc = pdfplumber.open(pdf_file)
            text = ""
            for page in doc.pages:
                try:
                    page_text = page.extract_text()
                    if not page_text.strip():  # Fallback for scanned PDFs
                        page_text = page.extract_text(x_tolerance=2)
                    text += page_text + "\n"
                except Exception:
                    continue  # Skip problematic pages
            doc.close()
            return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
    finally:
        file.file.seek(0)

def extract_text_from_docx(file: UploadFile) -> str:
    """Extracts text from DOCX with proper cleanup"""
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name
        
        # Process and clean up
        text = docx2txt.process(tmp_path)
        os.unlink(tmp_path)  # Delete temp file
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing DOCX: {str(e)}")
    finally:
        file.file.seek(0)

@app.post("/api/summarize")
async def summarize_text(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None, alias="text")
):
    """Handle both text and file upload summarization with enhanced validation"""
    # Check if we're getting Swagger UI's text input in the wrong field
    if isinstance(file, str):
        text = file
        file = None
    
    if not text and not file:
        raise HTTPException(status_code=400, detail="Either text or file must be provided")
    
    try:
        content = ""
        if file:
            filename = file.filename.lower()
            if filename.endswith(".pdf"):
                content = extract_text_from_pdf(file)
            elif filename.endswith(".docx"):
                content = extract_text_from_docx(file)
            elif filename.endswith(".txt"):
                content = (await file.read()).decode("utf-8")
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")
        else:
            content = text

        if not content.strip():
            raise HTTPException(status_code=400, detail="No readable content found")

        # Validate content length
        MAX_INPUT_LENGTH = 16000
        if len(content) > MAX_INPUT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Document too large. Max allowed: {MAX_INPUT_LENGTH} characters"
            )

        summary = await summarize(content)
        return {"summary": summary}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))