import re
import unicodedata

class TextCleaner:
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Cleans 'dirty' text from copy-pastes:
        1. Normalizes unicode characters.
        2. Removes non-printable control characters.
        3. Normalizes whitespace (multiple spaces/newlines into single ones).
        """
        if not text:
            return ""
            
        # Normalize unicode (e.g., curly quotes to straight quotes)
        text = unicodedata.normalize("NFKC", text)
        
        # Remove control characters (except newlines and tabs)
        text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in "\n\t")
        
        # Replace multiple newlines with a single one to save tokens
        text = re.sub(r'\n+', '\n', text)
        
        # Replace multiple spaces with a single one
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
