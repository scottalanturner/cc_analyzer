import anthropic
import pandas as pd
from typing import List, Dict
import base64
import os
import logging

logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

class PDFExtractionError(Exception):
    """Custom exception for PDF extraction errors"""
    pass

class PDFExtractor:
    def __init__(self, config):
        self.client = anthropic.Anthropic(
            api_key=config.anthropic_api_key,
            # Enable PDF support beta
            default_headers={"anthropic-beta": "pdfs-2024-09-25"}
        )
        self.config = config
        
    def extract_transactions_from_pdf(self, file_path: str) -> List[Dict]:
        """Extract transactions directly from PDF using Claude"""
        try:
            # Construct full path
            full_path = self.config.upload_dir / file_path
            logging.debug(f"Processing PDF: {full_path}")
            
            if not full_path.exists():
                raise PDFExtractionError(f"PDF file not found: {file_path}")
                
            if os.path.getsize(full_path) == 0:
                raise PDFExtractionError(f"File is empty: {file_path}")
            
            # Read PDF file and encode as base64
            with open(full_path, 'rb') as file:
                pdf_data = base64.b64encode(file.read()).decode('utf-8')
                
            # Send to Claude for direct transaction extraction
            system_prompt = """You are a helpful assistant that extracts credit card transactions from statements.
            Extract all transactions and return them in this JSON format:
            [{"date": "YYYY-MM-DD", "merchant": "Merchant Name", "amount": 123.45}, ...]
            Only include the JSON array in your response, no other text."""
            
            response = self.client.messages.create(
                model=self.config.anthropic_model,
                max_tokens=4096,
                temperature=0,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all transactions from this credit card statement and return them in JSON format."
                            },
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_data
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Parse the response into Python objects
            import json
            transactions = json.loads(response.content[0].text)
            return transactions
            
        except Exception as e:
            raise PDFExtractionError(f"Failed to extract transactions from PDF: {str(e)}")
    
    def create_dataframe(self, transactions: List[Dict]) -> pd.DataFrame:
        """Convert transactions to pandas DataFrame"""
        df = pd.DataFrame(transactions)
        return df