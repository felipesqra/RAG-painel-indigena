import httpx
from typing import Dict, Any
from .config import settings

async def fetch_api_data(dsei: str, data_init: str, data_end: str) -> Dict[str, Any]:
    url = settings.API_URL
    timeout = settings.API_TIMEOUT_SECONDS
    payload = {
        "dsei": dsei,
        "data_init": data_init,
        "data_end": data_end
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        return {"error": "API request timed out."}
    except httpx.HTTPStatusError as e:
        return {"error": f"API request failed with status {e.response.status_code}"}
    except httpx.RequestError as e:
        return {"error": f"An error occurred while requesting {e.request.url!r}."}
    except ValueError:
        return {"error": "Invalid JSON response from API."}
    except Exception as e:
        # Never crash the app with unhandled exceptions
        return {"error": f"Unexpected error: {str(e)}"}
