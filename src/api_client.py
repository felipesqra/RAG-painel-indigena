import httpx
from typing import Dict, Any
from .config import settings

def normalize_url(value: str, env_name: str) -> str:
    url = value.strip()
    if any(ord(char) < 32 or ord(char) == 127 for char in url):
        raise ValueError(f"{env_name} contem caracteres de controle. Remova quebras de linha ou espacos dentro da URL.")
    return url

async def fetch_api_data(dsei: str, data_init: str, data_end: str) -> Dict[str, Any]:
    timeout = settings.API_TIMEOUT_SECONDS
    params = {
        "dsei": dsei,
        "data_init": data_init,
        "data_end": data_end
    }

    try:
        url = normalize_url(settings.API_URL, "API_URL")
    except ValueError as e:
        return {"error": str(e)}

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if settings.API_METHOD.upper() == "POST":
                response = await client.post(url, json=params)
            else:
                response = await client.get(url, params=params)
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
