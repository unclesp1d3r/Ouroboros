from typing import ClassVar
from uuid import uuid4

from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy.ext.mutable import MutableDict, MutableList

from app.models.attack import AttackMode
from app.models.attack_resource_file import AttackResourceFile, AttackResourceType


class AttackResourceFileFactory(SQLAlchemyFactory[AttackResourceFile]):
    __model__ = AttackResourceFile
    __async_session__ = None
    __check_model__ = False
    __set_relationships__ = False
    __set_association_proxy__ = False
    file_name = "test_resource.txt"
    download_url = "https://example.com/resource.txt"
    checksum = "deadbeef" * 8  # 64 chars
    guid = Use(uuid4)
    resource_type = AttackResourceType.WORD_LIST
    line_format = "freeform"
    line_encoding = "utf-8"
    used_for_modes: ClassVar[list[AttackMode]] = [AttackMode.DICTIONARY]
    source = "upload"
    line_count = 10
    byte_size = 100
    project_id = None
    is_uploaded = False
    file_label = None
    tags = None

    # Add a classmethod for ephemeral wordlist
    @classmethod
    def ephemeral_wordlist(cls, **kwargs) -> AttackResourceFile:  # noqa: ANN003
        return cls.build(
            resource_type=AttackResourceType.EPHEMERAL_WORD_LIST,
            source="ephemeral",
            file_name="ephemeral_wordlist.txt",
            download_url="",
            checksum="",
            content=MutableDict({"lines": MutableList(["password1", "password2"])}),
            line_count=2,
            byte_size=20,
            **kwargs,
        )

    @classmethod
    def ephemeral_masklist(cls, **kwargs) -> AttackResourceFile:  # noqa: ANN003
        return cls.build(
            resource_type=AttackResourceType.EPHEMERAL_MASK_LIST,
            source="ephemeral",
            file_name="ephemeral_masklist.txt",
            download_url="",
            checksum="",
            content=MutableDict({"lines": ["?d?d?d?d", "?l?l?l?l"]}),
            line_count=2,
            byte_size=20,
            **kwargs,
        )


def test_ephemeral_masklist_factory() -> None:
    resource = AttackResourceFileFactory.ephemeral_masklist()
    assert resource.resource_type == AttackResourceType.EPHEMERAL_MASK_LIST
    assert resource.file_name == "ephemeral_masklist.txt"
    assert resource.content is not None
    assert resource.content["lines"] == ["?d?d?d?d", "?l?l?l?l"]
    assert resource.line_format in {"freeform", "mask"}
