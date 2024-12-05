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
- Store the extracted table from the PDF in a pandas dataframe
- The dataframe should have the following columns: date, merchant, amount
- The output of the program should print to the console

#TODO 3. Store data in database

#TODO 4. Analyze data

#TODO 5. Provide insights