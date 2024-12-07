from fastapi import FastAPI, BackgroundTasks
from typing import Dict

app = FastAPI()

async def process_pdf_background(file_path: str, notify_email: str):
    result = await process_pdf_async(file_path, notify_email)
    # Send email with results

@app.post("/process-pdf")
async def process_pdf(file_path: str, notify_email: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_pdf_background, file_path, notify_email)
    return {"status": "Processing started"} 