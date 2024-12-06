import argparse
import os
from config import Config
from pdf_extractor import PDFExtractor

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract transactions from PDF credit card statement')
    parser.add_argument('file_name', help='Name of the PDF file in uploads directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show verbose output')
    args = parser.parse_args()
    
    try:
        # Initialize config and extractor
        config = Config()
        extractor = PDFExtractor(config)
        
        # Construct full file path
        file_path = config.upload_dir / args.file_name
        
        if args.verbose:
            print(f"\nFile details:")
            print(f"Full path: {file_path}")
            print(f"File size: {os.path.getsize(file_path)} bytes")
            print(f"File exists: {os.path.exists(file_path)}")
        
        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        # Process the PDF
        print(f"Processing PDF file: {file_path}")
        
        # Extract text from PDF
        pdf_text = extractor.extract_text_from_pdf(file_path)
        print("PDF text extracted successfully")
        
        if args.verbose:
            print("\nExtracted text preview (first 500 chars):")
            print(pdf_text[:500])
        
        # Extract transactions using Claude
        transactions = extractor.extract_transactions(pdf_text)
        print(f"Found {len(transactions)} transactions")
        
        # Create DataFrame
        df = extractor.create_dataframe(transactions)
        print("\nExtracted Transactions:")
        print(df.to_string())
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 