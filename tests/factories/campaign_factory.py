from faker import Faker
from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.models.campaign import Campaign

fake = Faker()


class CampaignFactory(SQLAlchemyFactory[Campaign]):
    """
    Factory for creating Campaign models.

    Fields:
        - name (str): The name of the campaign.
        - description (str): The description of the campaign.
        - project_id (int): The ID of the project that the campaign belongs to.
        - priority (int): The priority of the campaign.
        - state (CampaignState): The state of the campaign.
        - is_unavailable (bool): Whether the campaign is unavailable. Only set to True if the campaign is created by the `HashUploadTask` model.
        - hash_list_id (int): The ID of the hash list that the campaign belongs to.
        - created_at (datetime): The creation timestamp of the campaign.
        - updated_at (datetime): The last update timestamp of the campaign.
    """

    __model__ = Campaign
    __async_session__ = None
    __check_model__ = False
    __set_relationships__ = False
    __set_association_proxy__ = False
    _name_counter = 0

    @classmethod
    def name(cls) -> str:
        cls._name_counter += 1
        return f"campaign-{cls.__faker__.uuid4()}-{cls._name_counter}"

    description = Use(fake.unique.sentence)
    project_id = None  # Must be set explicitly in tests

    @classmethod
    def hash_list_id(cls) -> int:
        """Require explicit hash_list_id to avoid null constraint violations."""
        raise ValueError(
            "hash_list_id must be set explicitly in tests. "
            "Use HashListFactory to create a hash list first, then pass hash_list_id=hash_list.id"
        )

    priority = 0
    state = None
    is_unavailable = False  # This field is only set to True if the campaign is created by the `HashUploadTask` model.
