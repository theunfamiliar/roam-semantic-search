from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.config import USERNAME, PASSWORD

security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    """
    Authenticate incoming requests using Basic Auth.
    
    Args:
        credentials: The HTTP Basic Auth credentials
        
    Returns:
        bool: True if authentication successful
        
    Raises:
        HTTPException: If authentication fails
    """
    is_username_valid = credentials.username == USERNAME
    is_password_valid = credentials.password == PASSWORD
    
    if not (is_username_valid and is_password_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized. Use correct Basic Auth.",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return True 