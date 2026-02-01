from fastapi import Depends
from jose import jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.logging import log_execution_block

# header
security = HTTPBearer()


@log_execution_block
def check_security(
    authorization: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    claim = jwt.decode(
        authorization.credentials,
        key="lfO8KbuHklqCLpYMczpxK5fm0fzcVVcAeRdrJEqN0Hk=",
        algorithms=["HS256"],
        audience="authenticated",
    )

    return claim
