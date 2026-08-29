from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",
    scheme_name="OAuth2PasswordBearer",
    scopes={"read": "Read access", "write": "Write access"}
)
