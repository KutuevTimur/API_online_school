from passlib.context import CryptContext


test_crypto_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

