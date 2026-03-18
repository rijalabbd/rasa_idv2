import os
import requests
import streamlit as st
from datetime import datetime

# =============================================================================
# Configuration
# =============================================================================

API_BASE_URL = os.environ.get("ADMIN_API_BASE_URL", "http://localhost:8000")
ADMIN_KEY = os.environ.get("ADMIN_KEY", "admin_secret_123")
API_TIMEOUT = 30  # seconds

def api_url(path: str) -> str:
    """Build full API URL from path."""
    base = API_BASE_URL.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return f"{base}/api/v1{path}"


def api_request(method: str, path: str, *, params=None, json=None, files=None, timeout=API_TIMEOUT) -> tuple:
    """
    Unified helper for API requests.
    Returns: (data_or_bytes, status_code, headers, content_type)
    """
    url = api_url(path)
    
    # Store request info for debug viewer
    st.session_state.last_request_info = {
        "method": method,
        "url": url,
        "time": datetime.now().strftime("%H:%M:%S")
    }
    
    try:
        resp = requests.request(
            method=method,
            url=url,
            params=params,
            json=json,
            files=files,
            timeout=timeout,
            headers={"X-ADMIN-KEY": ADMIN_KEY}
        )
        
        # Capture Request ID
        req_id = resp.headers.get("x-request-id")
        if req_id:
            st.session_state.last_request_id = req_id
        
        # Parse content
        content_type = resp.headers.get("content-type", "")
        
        if resp.status_code >= 400:
            # Handle error display
            err_data = None
            try:
                err_data = resp.json()
                detail = err_data.get("detail", resp.text)
                
                # Flatten nested detail if it's a dict (backend Pydantic/FastAPI structure)
                if isinstance(detail, dict):
                    detail = detail.get("detail", str(detail))
                
                code = err_data.get("code", "ERROR")
                st.toast(f"❌ {code}: {detail} (Ref: {req_id})")
            except:
                st.toast(f"❌ HTTP {resp.status_code}: {resp.text[:100]} (Ref: {req_id})")
            
            return (err_data, resp.status_code, resp.headers, content_type)
            
        # Success
        if "application/json" in content_type:
            return (resp.json(), resp.status_code, resp.headers, content_type)
        else:
            return (resp.content, resp.status_code, resp.headers, content_type)

    except requests.exceptions.ConnectionError:
        st.error(f"❌ Connection Error: Cannot reach {API_BASE_URL}")
        return (None, 0, {}, "")
    except requests.exceptions.Timeout:
        st.error(f"❌ Timeout Error: Request took longer than {timeout}s")
        return (None, 0, {}, "")
    except Exception as e:
        st.error(f"❌ Unexpected Error: {str(e)}")
        return (None, 0, {}, "")


def format_datetime(iso_str: str | None) -> str:
    """Format ISO datetime string for display."""
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, AttributeError):
        return iso_str
