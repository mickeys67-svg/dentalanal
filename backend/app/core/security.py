from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)


# NOTE: Authentication functions (get_current_user, get_optional_current_user) are defined
# in app.api.endpoints.auth module to avoid circular imports.
# They are re-exported from auth.py for use in other endpoints.
