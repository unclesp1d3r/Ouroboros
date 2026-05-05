from uuid import uuid4

from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy.ext.mutable import MutableDict, MutableList

from app.models.upload_resource_file import UploadResourceFile


class UploadResourceFileFactory(SQLAlchemyFactory[UploadResourceFile]):
    __model__ = UploadResourceFile
    __async_session__ = None
    __check_model__ = False
    __set_relationships__ = False
    __set_association_proxy__ = False
    file_name = "test_upload_resource.txt"
    download_url = "https://example.com/upload_resource.txt"
    checksum = "deadbeef" * 8  # 64 chars
    guid = Use(uuid4)
    line_format = "freeform"
    line_encoding = "utf-8"
    source = "upload"
    line_count = 10
    byte_size = 100
    project_id = None
    is_uploaded = False
    file_label = None
    tags = None
    content = MutableDict({"lines": MutableList(["hash1", "hash2"])})
