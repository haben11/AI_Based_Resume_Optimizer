import pypdf
import docx2txt
import io
from fastapi import UploadFile
from app.core.logging import logger
from app.utils.text_cleaner import TextCleaner

class FileParser:
    @staticmethod
    async def parse_file(file: UploadFile) -> str:
        content_type = file.content_type
        filename = file.filename
        
        logger.info("parsing_file", filename=filename, content_type=content_type)
        
        contents = await file.read()
        
        if content_type == "application/pdf":
            text = FileParser._parse_pdf(contents)
        elif content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
            text = FileParser._parse_docx(contents)
        elif content_type == "text/plain":
            text = contents.decode("utf-8")
        else:
            raise ValueError(f"Unsupported file type: {content_type}")
        
        # Clean the extracted text to remove control characters and normalize whitespace
        return TextCleaner.clean_text(text)

    @staticmethod
    def _parse_pdf(contents: bytes) -> str:
        pdf_reader = pypdf.PdfReader(io.BytesIO(contents))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        # Remove NUL characters that can cause JSON serialization errors
        text = text.replace('\x00', '')
        return text

    @staticmethod
    def _parse_docx(contents: bytes) -> str:
        return docx2txt.process(io.BytesIO(contents))
