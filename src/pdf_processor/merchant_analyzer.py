import pandas as pd
import os
from typing import List, Dict, Tuple
import anthropic
import requests
from dataclasses import dataclass
from dotenv import load_dotenv
import logging
import json

@dataclass
class ProductMatch:
    name: str
    price: float
    description: str
    confidence_score: float
    match_reason: str

@dataclass
class CompetitorProduct:
    name: str
    company: str
    price: str
    description: str
    website: str
    comparison: str

@dataclass
class MerchantInfo:
    merchant_code: str      # Original transaction description
    merchant: str          # Clean company name from website
    website: str
    phone: str
    product_description: str
    transaction_amount: float
    competitor_products: List[CompetitorProduct]
    original_transaction_description: str

class MerchantAnalyzer:
    def __init__(self, verbose: bool = False):
        load_dotenv()
        self.brave_api_key = os.getenv('BRAVE_API_KEY')
        self.claude_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.claude_model = os.getenv('ANTHROPIC_MODEL')
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
        self.logger.debug("Searching Brave for merchant: %s", merchant_name)
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {"X-Subscription-Token": self.brave_api_key}
        
        # Improve search query to focus on business information
        cleaned_name = merchant_name.strip().replace('*', '').lower()
        params = {
            "q": f'"{cleaned_name}" company business contact information',
            "count": 5  # Increased from 5 to get more results
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        self.logger.debug("Brave API response status: %d", response.status_code)
        
        if response.status_code == 200:
            results = response.json().get('web', {}).get('results', [])
            self.logger.debug("Found %d results from Brave", len(results))
            
            # Filter results to prioritize official websites
            filtered_results = []
            for result in results:
                url = result.get('url', '').lower()
                if any(term in url for term in ['.com', '.org', '.net', '.co']):
                    filtered_results.append(result)
            
            return filtered_results[:5]  # Return top 5 filtered results
        return []

    def _clean_merchant_code(self, merchant_code: str) -> str:
        """Clean up merchant code for better search results"""
        # Remove common transaction prefixes/suffixes
        cleaned = merchant_code.strip()
        cleaned = cleaned.split('*')[0]  # Remove everything after asterisk
        
        # Remove common transaction patterns
        patterns = ['TST', 'SQ ', 'SQU ', 'PAYPAL ', 'DEB ', 'ACH ', 'AUTOPAY']
        for pattern in patterns:
            cleaned = cleaned.replace(pattern, '')
        
        # Remove any non-alphanumeric chars except spaces
        cleaned = ''.join(c for c in cleaned if c.isalnum() or c.isspace())
        
        return cleaned.strip()

    def analyze_merchant(self, merchant_code: str, transaction_amount: float) -> MerchantInfo:
        """Analyze a single merchant using Brave search and Claude"""
        self.logger.info("Starting analysis for merchant: %s (amount: $%.2f)", 
                        merchant_code, transaction_amount)
        
        # Clean up merchant code before searching
        cleaned_merchant = self._clean_merchant_code(merchant_code)
        self.logger.debug("Cleaned merchant code: %s", cleaned_merchant)
        
        # Get search results with cleaned merchant name
        search_results = self.search_brave(cleaned_merchant)
        self.logger.debug("Got %d search results from Brave", len(search_results))
        
        merchant_context = "\n".join([
            f"URL: {result['url']}\n"
            f"Title: {result['title']}\n"
            f"Description: {result['description']}\n"
            for result in search_results
        ])
        self.logger.debug("Built merchant context:\n%s", merchant_context)

        # First prompt to get merchant info
        self.logger.debug("Sending merchant info prompt to Claude")
        merchant_prompt = f"""Based on these search results for the transaction '{merchant_code}', extract the company information:

Search Results:
{merchant_context}

Format your response exactly like this, with one piece of information per line:

Company name: [official name only]
Website URL: [url]
Phone number: [phone]
Products or services: [brief description]

If any information is unknown, use 'Unknown' as the value.
Focus on finding the official company name, as this will be used for further analysis."""
        
        merchant_response = self.client.messages.create(
            model=self.claude_model,
            max_tokens=1024,
            temperature=0,
            messages=[
                {"role": "user", "content": merchant_prompt}
            ]
        )
        self.logger.debug("Got merchant info response from Claude: %s", 
                         merchant_response.content[0].text)

        # Parse the first response to get company info
        merchant_analysis = merchant_response.content[0].text
        merchant_name = self.extract_field(merchant_analysis, "Company name")
        self.logger.debug("Extracted merchant name: %s", merchant_name)

        # Second prompt for competitor analysis
        self.logger.debug("Sending competitor analysis prompt to Claude")
        competitor_price_analysis_prompt = f"""
You are an AI assistant tasked with identifying less expensive competitor products based on transaction information. You will be given some company information, a transaction description, and a transaction amount. Your goal is to determine 1-3 competitor products that are less expensive than the given transaction.

Here is the information you will be working with:

<company_info>
{merchant_name}
</company_info>

<transaction_description>
{merchant_code}
</transaction_description>

<transaction_amount>
{transaction_amount}
</transaction_amount>

Follow these steps to complete the task:

1. Analyze the given information:
   - Identify the company name and any other relevant details from the company info.
   - Examine the transaction description to understand the type of product or service purchased.
   - Note the transaction amount as the reference price.

2. Research competitor products:
   - Based on the company name and transaction description, determine the industry or product category.
   - Search for similar products or services offered by other companies in the same industry.
   - Focus on finding options that are less expensive than the given transaction amount.

3. Select 1-3 competitor products:
   - Choose products that are similar in function or purpose to the original transaction.
   - Ensure that the selected products are less expensive than the transaction amount.
   - If possible, try to find options from well-known or reputable companies.

4. Gather information about each competitor product:
   - Product name
   - Company offering the product
   - Price (ensure it's less than the transaction amount)
   - Brief description of the product
   - Website or source of information (if available)

5. Present your findings:
   - Provide a brief introduction summarizing the original transaction and your task.
   - List each competitor product with the gathered information.
   - Explain how each product compares to the original transaction in terms of features and price.

Please format your response as a JSON object with the following structure:

{{
  "original_transaction": "Briefly describe the original transaction",
  "competitor_products": [[
    {{
      "product_name": "Product Name",
      "company": "Company Name",
      "price": "Price",
      "description": "Brief description",
      "website": "Website if available",
      "comparison": "How it compares to the original transaction"
    }}
  ]]
}}

Please include at least 1 and up to 3 competitor products in the array. If a website is not available, you may leave that field empty or null. Ensure the response is valid JSON that could be parsed by a program.

Remember to ensure that all competitor products you suggest are less expensive than the original transaction amount. If you cannot find any suitable competitor products that are less expensive, explain why in your answer.
"""

        competitor_price_analysis_response = self.client.messages.create(
            model=self.claude_model,
            max_tokens=1024,
            temperature=0,
            messages=[{"role": "user", "content": competitor_price_analysis_prompt}]
        )
        self.logger.debug("Got competitor analysis response from Claude: %s", 
                         competitor_price_analysis_response.content[0].text)

        # Parse responses
        merchant_analysis = merchant_response.content[0].text
        competitor_analysis = competitor_price_analysis_response.content[0].text
        
        self.logger.debug("Parsing competitor analysis")
        orig_trans, competitor_products = self._parse_competitor_analysis(competitor_analysis)
        self.logger.debug("Got %d competitor products", len(competitor_products))
        
        self.logger.debug("Creating MerchantInfo object")
        try:
            merchant_info = MerchantInfo(
                merchant_code=merchant_code,
                merchant=self.extract_field(merchant_analysis, "Company name"),
                website=self.extract_field(merchant_analysis, "Website URL"),
                phone=self.extract_field(merchant_analysis, "Phone number"),
                product_description=self.extract_field(merchant_analysis, "Products or services"),
                transaction_amount=transaction_amount,
                competitor_products=competitor_products,
                original_transaction_description=orig_trans
            )
            self.logger.info("Successfully created MerchantInfo for %s", merchant_info.merchant)
            return merchant_info
        except Exception as e:
            self.logger.error("Error creating MerchantInfo object: %s", str(e), exc_info=True)
            raise

    def extract_field(self, text: str, field: str) -> str:
        """Extract field value from Claude's response"""
        try:
            for line in text.split('\n'):
                if field.lower() in line.lower():
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        return parts[1].strip()
            return "Unknown"
        except (AttributeError, IndexError) as e:
            self.logger.error("Error extracting %s: %s", field, str(e))
            return "Unknown"

    def _parse_product_matches(self, analysis: str) -> List[ProductMatch]:
        matches = []
        sections = analysis.split('Product:')[1:]
        
        for section in sections:
            try:
                lines = [line.strip() for line in section.strip().split('\n') if line.strip()]
                name = lines[0].strip()
                price_line = lines[1].split('Price:')[1].strip()
                price = self._parse_price(price_line)
                
                description = next((line.split('Description:')[1].strip() 
                                 for line in lines if 'Description:' in line), 'Unknown')
                confidence = next((float(line.split('Confidence:')[1].strip().replace('%', ''))
                                for line in lines if 'Confidence:' in line), 0.0)
                reason = next((line.split('Reason:')[1].strip()
                             for line in lines if 'Reason:' in line), 'Unknown')
                
                matches.append(ProductMatch(
                    name=name, price=price, description=description,
                    confidence_score=confidence, match_reason=reason
                ))
            except (IndexError, ValueError, AttributeError) as e:
                self.logger.error("Error parsing product match section: %s", str(e))
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
            
        except (ValueError, AttributeError) as e:
            self.logger.error("Error parsing price '%s': %s", price_text, str(e))
            return 0.0

    def _parse_competitor_analysis(self, analysis: str) -> Tuple[str, List[CompetitorProduct]]:
        """Parse the competitor analysis response from Claude"""
        try:
            self.logger.debug("Raw analysis response: %s", analysis)
            
            # Find the JSON content
            try:
                answer_content = analysis.split('<answer>\n')[1].split('</answer>')[0].strip()
                self.logger.debug("Extracted content between answer tags: %s", answer_content)
            except IndexError:
                self.logger.warning("Could not find <answer> tags, trying to parse entire response")
                answer_content = analysis.strip()
            
            # Parse the JSON
            try:
                data = json.loads(answer_content)
                self.logger.debug("Successfully parsed JSON: %s", json.dumps(data, indent=2))
            except json.JSONDecodeError as e:
                self.logger.error("JSON parsing failed: %s\nContent was: %s", str(e), answer_content)
                return "", []
            
            # Extract original transaction description
            orig_trans = data.get('original_transaction', '')
            self.logger.debug("Extracted original transaction: %s", orig_trans)
            
            # Parse competitor products
            competitor_products = []
            for i, product in enumerate(data.get('competitor_products', [])):
                self.logger.debug("Processing competitor product %d: %s", i + 1, json.dumps(product, indent=2))
                try:
                    competitor_products.append(CompetitorProduct(
                        name=product.get('product_name', ''),
                        company=product.get('company', ''),
                        price=str(product.get('price', '')),
                        description=product.get('description', ''),
                        website=product.get('website', ''),
                        comparison=product.get('comparison', '')
                    ))
                    self.logger.debug("Successfully processed competitor product %d", i + 1)
                except Exception as e:
                    self.logger.error("Error processing competitor product %d: %s\nProduct data: %s", 
                                    i + 1, str(e), json.dumps(product, indent=2))
            
            self.logger.info("Successfully parsed %d competitor products", len(competitor_products))
            return orig_trans, competitor_products
            
        except Exception as e:
            self.logger.error("Error parsing competitor analysis: %s\nFull analysis: %s", 
                            str(e), analysis, exc_info=True)
            return "", []

    def analyze_transactions(self, csv_path: str, num_transactions: int = 5) -> List[MerchantInfo]:
        """Analyze merchants from a CSV file"""
        self.logger.info("Starting analysis of %d transactions from %s", num_transactions, csv_path)
        
        try:
            df = pd.read_csv(csv_path)
            self.logger.debug("Loaded CSV file with %d rows", len(df))
            
            merchant_data = df.groupby('merchant')['amount'].first().reset_index()
            merchant_data = merchant_data.head(num_transactions)
            self.logger.debug("Processing %d unique merchants", len(merchant_data))
            
            results = []
            for _, row in merchant_data.iterrows():
                try:
                    self.logger.info("Processing transaction: %s - $%.2f", row['merchant'], row['amount'])
                    merchant_info = self.analyze_merchant(row['merchant'], row['amount'])
                    results.append(merchant_info)
                except (requests.RequestException, anthropic.APIError) as e:
                    self.logger.error("Error analyzing merchant %s: %s", row['merchant'], str(e))
            
            self.logger.info("Analysis complete. Processed %d merchants successfully", len(results))
            return results
            
        except (pd.errors.EmptyDataError, FileNotFoundError, pd.errors.ParserError) as e:
            self.logger.error("Error processing CSV file: %s", str(e))
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
        print(f"\nOriginal Transaction: {result.original_transaction_description}")
        
        print("\nCompetitor Products:")
        for product in result.competitor_products:
            print(f"\n{product.name} by {product.company}")
            print(f"  Price: {product.price}")
            print(f"  Description: {product.description}")
            print(f"  Website: {product.website}")
            print(f"  Comparison: {product.comparison}")

if __name__ == "__main__":
    main() 