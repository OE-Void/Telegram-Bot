import os
import dotenv
from typing import Final, Dict
from datetime import datetime

# Load environment variables
dotenv.load_dotenv()

# Bot Configuration
TOKEN: Final = os.getenv('BOT_TOKEN')
BOT_USERNAME: Final = '@XenArcAI_Bot'

# Validation
if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables. Please check your .env file.")
