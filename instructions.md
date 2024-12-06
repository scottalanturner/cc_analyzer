This project is going to analyze customer credit card statements that are uploaded in PDF format. 

The goal is to extract the data from the PDF and store it in a database.

The data will be used to analyze the customer's business, and offer insights on how to reduce their business expenses. Insights can consist of the following list of options: 

- Finding lower-priced plans for services that they're already using
- Offering recommendations for similar services
- Crafting emails or support requests to the vendors used, asking for fee reductions or credits
- Offering recommendations for new services that they might be able to use
- Offering recommendations for combining two or more services
- Offering recommendations for automating their business tasks

You will be using the following frontend technologies:

Next.js
React
TailwindCSS
WebSocket client

You will be using the following backend technologies:

Python
AWS Lambda
API Gateway (REST and WebSocket)
Aurora (MySQL)

# Core functionalities
1. Upload PDF statement
  - Create a drag-and-drop upload zone component
  - Use React and TailwindCSS
  - Show a dashed border box with centered text "Drag and drop your PDF statement here"
  - Show an icon above the text (PDF or upload icon)
  - Accept only PDF files
  - Show visual feedback when file is dragged over (highlight border)
  - Show loading state while uploading
  - Show success/error messages
  - Allow clicking to open file picker as alternative

- Create API endpoint to handle file upload
  - POST /api/upload
  - Accept multipart/form-data
  - Validate file is PDF
  - Store in a local directory

- Create WebSocket connection
  - Connect when upload starts
  - Send progress updates during upload
  - Send completion status
  - Handle reconnection if disconnected


2. Extract data from PDF
- Create a test class that can extract data from a PDF file
- The test class should have a main method that can be run from the command line
- The program should take a file path as a command line argument
- The program should submit the PDF to the Anthropic Claude API for text extraction. 
- The api keys should be stored in the environment variables
- A config class should be created to load the api keys from the environment variables, both in a dev and production environment
- Store the extracted table from the PDF in a pandas dataframe
- The dataframe should have the following columns: date, merchant, amount
- The output of the program should print to the console
- Use object-oriented programming to create the classes

3. Analyzing credit card merchants and fetching information using Claude and Brave
- Create a test class that can analyze the credit card transaction data
- The test class should have a main method that can be run from the command line
- The program should take a file path as a command line argument
- Load the data from the CSV file into a pandas dataframe
- Take an argument for the number of transactions to analyze
- For the number of transactions to analyze, fetch the merchant information using the Brave Search API and Claude API
- Search for the merchant name with the Brave search API
- Inject search results into prompt
- Answer the user's questions with Claude
- Print the results to the console
- Use object-oriented programming to create the classes

#TODO 5. Provide insights


# Documentation and Code Examples

## User's questions
- What is the merchant website?
- What is the merchant's phone number?
- What product or service matches the charges for the transactions?
- What is the description of the product or service?

## Analyzing credit card merchants

Purpose: Retrieve merchant information from the merchant description field.

Use the Brave Search API to retrieve merchant information. This is a code example of connecting to the Brave Search API and Anthropic Claude API:
https://github.com/anthropics/anthropic-cookbook/blob/main/third_party/Brave/web_search_using_brave.ipynb