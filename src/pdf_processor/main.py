import argparse
import os
from config import Config
from pdf_extractor import PDFExtractor, PDFExtractionError
from typing import Dict, Any
import sys

def process_pdf(file_path: str, notify_email: str) -> Dict[str, Any]:
    try:
        # Initialize config and extractor
        config = Config()
        extractor = PDFExtractor(config)
        
        # Extract transactions directly from PDF
        transactions = extractor.extract_transactions_from_pdf(file_path)
        
        # Create DataFrame
        df = extractor.create_dataframe(transactions)
        
        return {
            "success": True,
            "num_transactions": len(transactions),
            "email": notify_email,
            "transactions": transactions
        }
        
    except PDFExtractionError as e:
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }

# Lambda handler
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    file_path = event['file_path']
    notify_email = event['notify_email']
    
    return process_pdf(file_path, notify_email)

# Local development entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('file_name', help='Name of the PDF file in uploads directory')
    parser.add_argument('--email', help='Email to notify when complete')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    
    try:
        result = process_pdf(args.file_name, args.email)
        
        if not result["success"]:
            print(f"Error: {result['error']}")
            sys.exit(1)
            
        print(f"Processing complete: {result}")
        
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1) 