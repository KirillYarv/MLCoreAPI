from src.repository.DbInfoRepository import DbInfoRepository


class DbConnectionService:
    """Application service for database connectivity checks."""

    def __init__(self, db_info_repo: DbInfoRepository) -> None:
        """Initialize service.

        Args:
            db_info_repo: Repository that performs DB-level connectivity checks.
        """
        self.db_info_repo = db_info_repo

    def check_connection(self) -> dict:
        """Return API-friendly connectivity status payload.

        Returns:
            dict: JSON-serializable payload with keys:
                - is_connected (bool)
                - message (str)
        """
        connected, message = self.db_info_repo.is_connected()
        return {"is_connected": connected, "message": message}
