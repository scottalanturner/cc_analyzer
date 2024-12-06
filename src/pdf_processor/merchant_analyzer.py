import pandas as pd
import os
from typing import List, Dict
import anthropic
import requests
from dataclasses import dataclass
from dotenv import load_dotenv
import logging

@dataclass
class ProductMatch:
    name: str
    price: float
    description: str
    confidence_score: float
    match_reason: str

@dataclass
class MerchantInfo:
    merchant_code: str  # Original transaction description
    merchant: str      # Clean company name from website
    website: str
    phone: str
    product_description: str
    price_range: str
    transaction_amount: float
    likely_purchases: List[ProductMatch]  # List of potential matches

class MerchantAnalyzer:
    def __init__(self, verbose: bool = False):
        load_dotenv()
        self.brave_api_key = os.getenv('BRAVE_API_KEY')
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.client = anthropic.Anthropic(api_key=self.claude_api_key)
        
        # Setup logging
        self.logger = logging.getLogger('MerchantAnalyzer')
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
    def search_brave(self, merchant_name: str) -> List[Dict]:
        """Search Brave for merchant information"""
        self.logger.debug(f"Searching Brave for merchant: {merchant_name}")
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"X-Subscription-Token": self.brave_api_key}
        params = {
            "q": f"{merchant_name} business information contact",
            "count": 5
        }
        
        response = requests.get(url, headers=headers, params=params)
        self.logger.debug(f"Brave API response status: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json().get('web', {}).get('results', [])
            self.logger.debug(f"Found {len(results)} results from Brave")
            return results
        return []

    def analyze_merchant(self, merchant_code: str, transaction_amount: float) -> MerchantInfo:
        """Analyze a single merchant using Brave search and Claude"""
        self.logger.info(f"Analyzing merchant: {merchant_code}")
        
        # Get search results
        search_results = self.search_brave(merchant_code)
        self.logger.debug(f"Processing {len(search_results)} search results")
        
        merchant_context = "\n".join([
            f"URL: {result['url']}\n"
            f"Title: {result['title']}\n"
            f"Description: {result['description']}\n"
            for result in search_results
        ])

        # First prompt for merchant info
        self.logger.debug("Sending merchant info prompt to Claude")
        merchant_prompt = f"""Based on these search results about {merchant_code}, provide the following information.
Format your response exactly like this, with one piece of information per line:

Company name: [official name only]
Website URL: [url]
Phone number: [phone]
Products or services: [brief description]
Price range: [range]

If any information is unknown, use 'Unknown' as the value."""

        merchant_response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": merchant_prompt}]
        )
        
        # Calculate price range for analysis
        amount = transaction_amount
        buffer = amount * 0.15  # 15% buffer for tax/shipping/fees
        min_amount = amount - buffer
        max_amount = amount + buffer

        # Second prompt for purchase analysis
        self.logger.debug("Sending purchase analysis prompt to Claude")
        purchase_prompt = f"""Based on these search results about {merchant_code}:

{merchant_context}

The customer made a purchase for ${amount:.2f} (including possible taxes/fees).
Analyze likely products/services between ${min_amount:.2f}-${max_amount:.2f}.

List up to 3 matches in exactly this format:

Product: [exact product/service name]
Price: [exact price in $XX.XX format, or $XX.XX-$YY.XX for ranges]
Description: [brief description]
Confidence: [number]%
Reason: [brief explanation]

Consider:
- Base price before tax/shipping
- Common bundles or packages
- Subscription periods (monthly/annual)
- Regional price variations
- Typical discounts"""

        purchase_response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": purchase_prompt}]
        )

        # Parse responses
        merchant_analysis = merchant_response.content[0].text
        purchase_analysis = purchase_response.content[0].text
        
        self.logger.debug("Parsing merchant information")
        merchant_info = MerchantInfo(
            merchant_code=merchant_code,
            merchant=self.extract_field(merchant_analysis, "Company name"),
            website=self.extract_field(merchant_analysis, "Website URL"),
            phone=self.extract_field(merchant_analysis, "Phone number"),
            product_description=self.extract_field(merchant_analysis, "Products or services"),
            price_range=self.extract_field(merchant_analysis, "Price range"),
            transaction_amount=transaction_amount,
            likely_purchases=self._parse_product_matches(purchase_analysis)
        )
        
        self.logger.debug(f"Merchant analysis complete: {merchant_info.merchant}")
        return merchant_info

    def extract_field(self, text: str, field: str) -> str:
        """Extract field value from Claude's response"""
        try:
            for line in text.split('\n'):
                if field.lower() in line.lower():
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        return parts[1].strip()
            return "Unknown"
        except Exception as e:
            self.logger.error(f"Error extracting {field}: {str(e)}")
            return "Unknown"

    def _parse_product_matches(self, analysis: str) -> List[ProductMatch]:
        """Parse Claude's product match analysis into structured data"""
        matches = []
        
        # Split the analysis into sections for each product match
        sections = analysis.split('Product:')[1:]  # Skip the first split as it's empty
        
        for section in sections:
            try:
                lines = [line.strip() for line in section.strip().split('\n') if line.strip()]
                
                # Extract name from first line
                name = lines[0].strip()
                
                # Handle price ranges and convert to average price
                price_line = lines[1].split('Price:')[1].strip()
                price = self._parse_price(price_line)
                
                # Extract remaining fields
                description = next((line.split('Description:')[1].strip() 
                                 for line in lines if 'Description:' in line), 'Unknown')
                
                confidence = next((float(line.split('Confidence:')[1].strip().replace('%', ''))
                                for line in lines if 'Confidence:' in line), 0.0)
                
                reason = next((line.split('Reason:')[1].strip()
                             for line in lines if 'Reason:' in line), 'Unknown')
                
                matches.append(ProductMatch(
                    name=name,
                    price=price,
                    description=description,
                    confidence_score=confidence,
                    match_reason=reason
                ))
            except Exception as e:
                print(f"Error parsing product match section: {str(e)}")
                continue
                
        return matches

    def _parse_price(self, price_text: str) -> float:
        """Parse price text that might contain ranges or approximations"""
        try:
            # Remove currency symbols and whitespace
            price_text = price_text.replace('$', '').strip()
            
            # Handle approximate prices
            price_text = price_text.replace('~', '').strip()
            
            # Handle price ranges by taking the average
            if '-' in price_text:
                low, high = price_text.split('-')
                # Extract just the numbers from each part
                low = float(''.join(c for c in low if c.isdigit() or c == '.'))
                high = float(''.join(c for c in high if c.isdigit() or c == '.'))
                return (low + high) / 2
            
            # Handle monthly prices
            if '/month' in price_text:
                price_text = price_text.split('/month')[0].strip()
                
            # Extract just the numbers
            price = float(''.join(c for c in price_text if c.isdigit() or c == '.'))
            return price
            
        except Exception as e:
            print(f"Error parsing price '{price_text}': {str(e)}")
            return 0.0

    def analyze_transactions(self, csv_path: str, num_transactions: int = 5) -> List[MerchantInfo]:
        """Analyze merchants from a CSV file"""
        self.logger.info(f"Starting analysis of {num_transactions} transactions from {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            self.logger.debug(f"Loaded CSV file with {len(df)} rows")
            
            merchant_data = df.groupby('merchant')['amount'].first().reset_index()
            merchant_data = merchant_data.head(num_transactions)
            self.logger.debug(f"Processing {len(merchant_data)} unique merchants")
            
            results = []
            for _, row in merchant_data.iterrows():
                try:
                    self.logger.info(f"Processing transaction: {row['merchant']} - ${row['amount']:.2f}")
                    merchant_info = self.analyze_merchant(row['merchant'], row['amount'])
                    results.append(merchant_info)
                except Exception as e:
                    self.logger.error(f"Error analyzing merchant {row['merchant']}: {str(e)}", exc_info=True)
            
            self.logger.info(f"Analysis complete. Processed {len(results)} merchants successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing CSV file: {str(e)}", exc_info=True)
            raise

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze merchant information from credit card transactions')
    parser.add_argument('csv_path', help='Path to the CSV file containing transactions')
    parser.add_argument('--num-transactions', type=int, default=5, 
                        help='Number of transactions to analyze')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    analyzer = MerchantAnalyzer(verbose=args.verbose)
    results = analyzer.analyze_transactions(args.csv_path, args.num_transactions)
    
    # Print results
    for result in results:
        print("\n" + "="*50)
        print(f"Transaction Description: {result.merchant_code}")
        print(f"Company Name: {result.merchant}")
        print(f"Transaction Amount: ${result.transaction_amount:.2f}")
        print(f"Website: {result.website}")
        print(f"Phone: {result.phone}")
        print(f"Products/Services: {result.product_description}")
        print(f"Typical Price Range: {result.price_range}")
        
        print("\nLikely Purchases:")
        for purchase in result.likely_purchases:
            print("\n  Product Match:")
            print(f"  - Name: {purchase.name}")
            print(f"  - Listed Price: ${purchase.price:.2f}")
            print(f"  - Description: {purchase.description}")
            print(f"  - Confidence: {purchase.confidence_score}%")
            print(f"  - Reason: {purchase.match_reason}")

if __name__ == "__main__":
    main() 