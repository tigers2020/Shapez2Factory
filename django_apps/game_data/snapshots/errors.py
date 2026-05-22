from enum import StrEnum


class SnapshotBuildErrorCode(StrEnum):
    NO_IMPORT_BATCH = "no_import_batch"
    ORPHAN_FOOTPRINT = "orphan_footprint"
    ORPHAN_CONNECTOR = "orphan_connector"
    ORPHAN_TRANSPORT = "orphan_transport"


class SnapshotBuildError(Exception):
    def __init__(self, code: SnapshotBuildErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)
