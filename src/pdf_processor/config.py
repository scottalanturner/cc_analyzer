from typing import Optional
import os
from dotenv import load_dotenv
from pathlib import Path

class Config:
    def __init__(self):
        # Load environment variables from .env file in development
        if os.getenv('ENVIRONMENT') != 'production':
            load_dotenv()
        
        # Get project root directory (2 levels up from this file)
        self.project_root = Path(__file__).parent.parent.parent
        
        # Define upload directory
        self.upload_dir = self.project_root / 'uploads'
        
        # Create uploads directory if it doesn't exist
        self.upload_dir.mkdir(exist_ok=True)
        
        self.anthropic_api_key: Optional[str] = os.getenv('ANTHROPIC_API_KEY')
        
        if not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set") 
        
        # Model configuration
        self.anthropic_model = os.getenv('ANTHROPIC_MODEL')
        
        # Directories
        self.base_dir = Path(__file__).parent.parent.parent
        self.upload_dir = self.base_dir / 'uploads'
        
        # Create uploads directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)