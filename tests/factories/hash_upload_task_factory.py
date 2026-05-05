from datetime import UTC, datetime
from uuid import uuid4

from polyfactory import Use
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.models.hash_upload_task import (
    HashUploadStatus,
    HashUploadTask,
)
from app.models.upload_error_entry import UploadErrorEntry


class HashUploadTaskFactory(SQLAlchemyFactory[HashUploadTask]):
    __model__ = HashUploadTask
    __async_session__ = None
    __check_model__ = False
    __set_relationships__ = False
    __set_association_proxy__ = False
    user_id = Use(uuid4)
    filename = "shadow.txt"
    status = HashUploadStatus.PENDING
    started_at = Use(lambda: datetime.now(UTC))
    finished_at = None
    error_count = 0
    hash_list_id = None  # Must be set explicitly in tests
    campaign_id = None  # Must be set explicitly in tests


class UploadErrorEntryFactory(SQLAlchemyFactory[UploadErrorEntry]):
    __model__ = UploadErrorEntry
    __async_session__ = None
    __check_model__ = False
    __set_relationships__ = False
    __set_association_proxy__ = False
    upload_id = None  # Must be set explicitly in tests
    line_number = 1
    raw_line = "badline"
    error_message = "Parse error"
