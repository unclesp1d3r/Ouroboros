# type: ignore[assignment]
from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.models.attack import Attack, AttackMode, AttackState

fake = Faker()


class AttackFactory(SQLAlchemyFactory[Attack]):
    __model__ = Attack
    __async_session__ = None
    __check_model__ = False
    __set_relationships__ = False
    __set_association_proxy__ = False
    _name_counter = 0
    _url_counter = 0
    _checksum_counter = 0

    @classmethod
    def name(cls) -> str:
        cls._name_counter += 1
        return f"attack-{cls.__faker__.uuid4()}-{cls._name_counter}"

    @classmethod
    def token(cls) -> str:
        return f"csa_{cls.__faker__.uuid4()}"

    @classmethod
    def hash_list_url(cls) -> str:
        cls._url_counter += 1
        return (
            f"https://example.com/hashlist/{cls._url_counter}-{cls.__faker__.uuid4()}"
        )

    @classmethod
    def hash_list_checksum(cls) -> str:
        cls._checksum_counter += 1
        # Ensure checksum never exceeds 64 chars
        val: str = f"checksum-{cls._checksum_counter}-{cls.__faker__.sha256()}"
        return val[:64]

    description = Use(fake.unique.sentence)
    state = AttackState.PENDING
    attack_mode = AttackMode.DICTIONARY
    attack_mode_hashcat = 0
    hash_mode = 0
    mask = None
    increment_mode = False
    increment_minimum = 0
    increment_maximum = 0
    optimized = False
    slow_candidate_generators = False
    workload_profile = 3
    disable_markov = False
    classic_markov = False
    markov_threshold = 0
    left_rule = None
    right_rule = None
    custom_charset_1 = None
    custom_charset_2 = None
    custom_charset_3 = None
    custom_charset_4 = None
    hash_list_id = 1
    word_list_id = None
    rule_list_id = None
    mask_list_id = None
    charset_id = None
    priority = 0
    template_id = None
    start_time = None
    end_time = None
    campaign_id = None  # Must be set explicitly in tests
    # hash_type_id is actually found on the hash_list, associated with the campaign

    # Relations must be set explicitly in tests if needed

    comment = None
    complexity_score = None
    modifiers = None

    # Don't try to override build or create_async methods
