import json
import os
from typing import Dict, Any
from .config import settings

def get_mock_data() -> Dict[str, Any]:
    mock_path = settings.MOCK_API_RESPONSE_PATH
    if not os.path.exists(mock_path):
        return {"error": f"Mock file not found at {mock_path}"}
    
    try:
        with open(mock_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Failed to load mock data: {str(e)}"}
