from typing import Tuple

import psycopg2


class DbInfoRepository:
    """Repository for lightweight database health checks.

    This class is intentionally isolated from ARL data access to keep
    responsibilities separated and make health-check logic reusable.
    """

    def __init__(
        self,
        database: str = "Recommendation",
        user: str = "postgres",
        password: str = "govgay111",
        host: str = "host.docker.internal",
        port: int = 5432,
    ) -> None:
        """Store database connection settings.

        Args:
            database: Target database name.
            user: Database user.
            password: Database password.
            host: Database host.
            port: Database port.
        """
        self.database = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port

    def is_connected(self) -> Tuple[bool, str]:
        """Check whether PostgreSQL is reachable with configured credentials.

        Returns:
            Tuple[bool, str]:
                - bool: True if connection succeeds, otherwise False.
                - str: Success message or error details.
        """
        connection = None
        try:
            connection = psycopg2.connect(
                database=self.database,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
            )
            return True, "Connection to database is successful"
        except Exception as error:
            return False, str(error)
        finally:
            if connection is not None:
                connection.close()
