# Credit Card Transaction Analyzer

The fastest way to analyze your credit card bills and banking statements to find alternative merchants and services to save money.

## Overview

This project provides a streamlined way to analyze credit card and banking statements, helping users find alternative merchants for their credit card spend.

## Features

- PDF file upload and processing
- Transaction data analysis
- Spending pattern visualization (TODO)
- Merchant categorization (TODO)    
- Date-based transaction filtering (TODO)

## Getting Started

### Prerequisites

- Python 3.x
- Poetry (for dependency management)
- Git
- Anthropic API Key ([Get it here](https://www.anthropic.com/product))
- Brave Search API Key ([Get it here](https://brave.com/search/api/))
- Credit card statement(s) (PDF format), from your personal account

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/scottalanturner/cc_analyzer.git
    cd cc_analyzer
    ```

2. Install dependencies using Poetry:
    ```bash
    poetry install
    ```

3. Create a `.env` file in the root directory with the following variables:
    ```
    ANTHROPIC_API_KEY=<your-anthropic-api-key>
    BRAVE_API_KEY=<your-brave-api-key>
    ```

### Usage

1. Start the application:
    ```bash
    npm run dev
   

2. Navigate to `http://localhost:3000` in your web browser

3. Drag & Drop your PDF credit card bill into the browser window

3. View the analysis and visualizations


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Security

This application is designed for personal use. Please be cautious when handling sensitive financial data and never commit real transaction data to the repository.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Anthropic](https://www.anthropic.com/) for the API that powers the AI analysis
- [Brave](https://brave.com/) for the API that powers the search functionality
- [Anthropic](https://www.anthropic.com/) for the PDF support

## Contact

Scott Alan Turner - [@scottalanturner](https://twitter.com/scottalanturner)

Project Link: [https://github.com/scottalanturner/cc_analyzer](https://github.com/scottalanturner/cc_analyzer)
 ```