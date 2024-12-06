import anthropic
import pandas as pd
from typing import List, Dict
import PyPDF2
import os

class PDFExtractor:
    def __init__(self, config):
        self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract raw text from PDF file"""
        try:
            # Verify file exists and has size > 0
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if os.path.getsize(file_path) == 0:
                raise ValueError(f"File is empty: {file_path}")
            
            text = ""
            with open(file_path, 'rb') as file:
                # Try to create PDF reader
                try:
                    pdf_reader = PyPDF2.PdfReader(file)
                except Exception as e:
                    raise ValueError(f"Failed to read PDF file. Make sure it's a valid PDF and not password protected. Error: {str(e)}")
                
                # Check if PDF has pages
                if len(pdf_reader.pages) == 0:
                    raise ValueError("PDF file contains no pages")
                
                # Extract text from each page
                for page in pdf_reader.pages:
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text
                    except Exception as e:
                        print(f"Warning: Failed to extract text from page. Error: {str(e)}")
                        continue
                    
            if not text.strip():
                raise ValueError("No text could be extracted from the PDF")
            
            return text
        
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def extract_transactions(self, pdf_text: str) -> List[Dict]:
        """Extract transactions using Claude API"""
        system_prompt = """You are a helpful assistant that extracts credit card transactions from statements.
        Extract all transactions and return them in this JSON format:
        [{"date": "YYYY-MM-DD", "merchant": "Merchant Name", "amount": 123.45}, ...]
        Only include the JSON array in your response, no other text."""
        
        message = f"Extract the transactions from this credit card statement: {pdf_text}"
        
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4096,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": message}]
        )
        
        # Parse the response into Python objects
        import json
        transactions = json.loads(response.content[0].text)
        return transactions
    
    def create_dataframe(self, transactions: List[Dict]) -> pd.DataFrame:
        """Convert transactions to pandas DataFrame"""
        df = pd.DataFrame(transactions)
        return df 