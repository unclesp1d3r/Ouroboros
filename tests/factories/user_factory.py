import secrets
from datetime import UTC, datetime

from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.core.auth import hash_password
from app.models.user import User, UserRole

fake = Faker()


class UserFactory(SQLAlchemyFactory[User]):
    __model__ = User
    __async_session__ = None
    __check_model__ = False
    __set_relationships__ = False
    __set_association_proxy__ = False
    _name_counter = 0
    _email_counter = 0

    @classmethod
    def name(cls) -> str:
        cls._name_counter += 1
        return f"user-{cls.__faker__.uuid4()}-{cls._name_counter}"

    @classmethod
    def email(cls) -> str:
        cls._email_counter += 1
        return f"user{cls._email_counter}-{cls.__faker__.uuid4()}@example.com"

    # Always use a valid bcrypt hash for 'password'
    # Use a lambda to generate hash at runtime to avoid class definition issues
    hashed_password = Use(lambda: hash_password("password"))
    is_active = True
    role = UserRole.ANALYST
    is_superuser = False
    reset_password_token = Use(lambda: fake.unique.uuid4())

    # Control API key field - generate realistic key
    @classmethod
    def api_key(cls) -> str:
        # Generate a realistic API key format: cst_<uuid>_<random>
        return f"cst_{cls.__faker__.uuid4()}_{secrets.token_hex(24)}"

    api_key_created_at = Use(lambda: datetime.now(UTC))
    # No FKs; pure factory.


# Don't try to override build or create_async methods
