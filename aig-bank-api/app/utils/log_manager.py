"""Log file management utility."""

from datetime import UTC, datetime
from pathlib import Path
import re
import shutil
import tempfile

from ..core.config import settings
from ..core.errors import ResourceNotFoundError


class LogManager:
    """Utility for managing and reading log files."""

    def __init__(self):
        """Initialize the LogManager.

        Uses the logs directory from application settings.
        """
        self.logs_dir = Path(settings.logs_directory)

    def _resolve_path(self, filename: str) -> Path:
        """Resolve log file path and validate it exists.

        Args:
            filename: Name of the log file (already validated by schema)

        Returns:
            Path: Resolved path to the log file

        Raises:
            ResourceNotFoundError: If file does not exist
        """
        file_path = self.logs_dir / filename
        resolved = file_path.resolve()

        if not resolved.exists():
            raise ResourceNotFoundError("LogFile", filename)

        return resolved

    def list_files(self) -> list[dict]:
        """List all log files in the logs directory.

        Returns:
            list[dict]: List of file information dictionaries with keys:
                - filename: str
                - size_bytes: int
                - modified_at: datetime
        """
        files_info = []

        if not self.logs_dir.exists():
            return files_info

        for file_path in self.logs_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files_info.append(
                    {
                        "filename": file_path.name,
                        "size_bytes": stat.st_size,
                        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                    }
                )
        files_info.sort(key=lambda x: x["filename"])
        return files_info

    def get_parsed_content(self, filename: str, max_lines: int = 1000) -> dict:
        """Read and parse INFO level log entries from a specific log file.

        Args:
            filename: Name of the log file (already validated by schema)
            max_lines: Maximum number of lines to return

        Returns:
            dict: Dictionary with keys:
                - filename: str
                - lines: list[str]
                - total_lines: int
                - returned_lines: int

        Raises:
            ResourceNotFoundError: If log file not found
        """
        resolved_path = self._resolve_path(filename)

        info_lines = []
        total_info_lines = 0
        info_log_pattern = re.compile(r".* - INFO - .*")

        with open(resolved_path, encoding="utf-8") as f:
            all_lines = f.readlines()
            for line in all_lines:
                if info_log_pattern.match(line):
                    total_info_lines += 1
                    info_lines.append(line.strip())

        returned_lines = info_lines[-max_lines:] if len(info_lines) > max_lines else info_lines

        return {
            "filename": filename,
            "lines": returned_lines,
            "total_lines": total_info_lines,
            "returned_lines": len(returned_lines),
        }

    def get_file_path(self, filename: str) -> Path:
        """Get the path to a log file for download.

        Creates a temporary snapshot of the log file to avoid race conditions
        where the file is being written to while being downloaded.

        Args:
            filename: Name of the log file (already validated by schema)

        Returns:
            Path: Path to a temporary snapshot of the log file

        Raises:
            ResourceNotFoundError: If file does not exist

        Note:
            The caller is responsible for cleaning up the temporary file.
        """
        print(filename)
        resolved_path = self._resolve_path(filename)
        print(resolved_path)

        suffix = resolved_path.suffix
        with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False, prefix=f"log_download_{resolved_path.stem}_") as temp_file:
            try:
                with open(resolved_path, "rb") as src:
                    shutil.copyfileobj(src, temp_file)
                return Path(temp_file.name)
            except Exception:
                Path(temp_file.name).unlink(missing_ok=True)
                raise


__all__ = ["LogManager"]
