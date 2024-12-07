from celery import Celery
import asyncio

app = Celery('pdf_processor',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')

@app.task
def process_pdf_task(file_path: str, notify_email: str):
    # Reuse the same processing logic
    result = asyncio.run(process_pdf_async(file_path, notify_email))
    return result 