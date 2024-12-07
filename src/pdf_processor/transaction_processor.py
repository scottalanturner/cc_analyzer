import asyncio
import json
from typing import List, Dict, Any
import logging
from merchant_analyzer import MerchantAnalyzer, MerchantInfo
from config import Config

class TransactionProcessor:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.logger = logging.getLogger('TransactionProcessor')
        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    async def process_transaction(self, merchant: str, amount: float) -> MerchantInfo:
        """Process a single transaction asynchronously"""
        self.logger.debug("Processing transaction: %s - $%.2f", merchant, amount)
        analyzer = MerchantAnalyzer(verbose=self.verbose)
        
        # Create a new event loop for the thread
        loop = asyncio.get_event_loop()
        # Run the merchant analysis in the executor to prevent blocking
        merchant_info = await loop.run_in_executor(
            None, analyzer.analyze_merchant, merchant, amount
        )
        return merchant_info

    async def process_transactions(self, transactions: List[Dict[str, Any]]) -> List[MerchantInfo]:
        """Process all transactions in parallel"""
        self.logger.info("Processing %d transactions", len(transactions))

        # Create tasks for all transactions
        tasks = []
        processing_count = 0
        for transaction in transactions:
            # Skip automatic payments or credits (negative amounts)
            if ('AUTOMATIC PAYMENT' in transaction['merchant'] or 
                transaction['amount'] < 0):
                continue
                
            task = asyncio.create_task(
                self.process_transaction(
                    transaction['merchant'],
                    transaction['amount']
                )
            )
            tasks.append(task)
            # just process 2 transactions for now
            processing_count += 1
            if processing_count == 2:
                break

        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out any exceptions and log them
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                self.logger.error("Error processing transaction: %s", str(result))
            else:
                processed_results.append(result)

        return processed_results

def process_json_file(json_path: str, verbose: bool = False) -> List[MerchantInfo]:
    """Process transactions from a JSON file"""
    processor = TransactionProcessor(verbose=verbose)
    config = Config()
    
    # Construct full path from uploads directory
    full_path = config.upload_dir / json_path
    logging.debug("Processing json: %s", full_path)
    
    # Read JSON file
    with open(full_path, 'r') as f:
        try:
            json_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {str(e)}") from e

    # Run the async processing
    return asyncio.run(processor.process_transactions(json_data['transactions']))

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Process transactions in parallel')
    parser.add_argument('json_path', help='Path to the JSON file containing transactions')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    try:
        results = process_json_file(args.json_path, args.verbose)
        
        # Print results
        print(f"\nProcessed {len(results)} transactions successfully")
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
                
    except Exception as e:
        print(f"Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main() 