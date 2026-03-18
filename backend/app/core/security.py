import os
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-ADMIN-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_admin_api_key(api_key: str = Security(api_key_header)):
    """
    Validates X-ADMIN-KEY header.
    Returns the key if valid, else raises 401.
    """
    settings_admin_key = os.environ.get("ADMIN_KEY")
    
    if not settings_admin_key:
        # Fail open or closed? If key not set, better strictly fail or log error.
        # For this phase, we assume env is set.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: ADMIN_KEY not set",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key == settings_admin_key:
        return api_key
    
    # Contract: {"detail":"Unauthorized","code":"UNAUTHORIZED","context":{}}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "detail": "Unauthorized",
            "code": "UNAUTHORIZED",
            "context": {}
        }
    )
