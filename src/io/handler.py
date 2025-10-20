from pathlib import Path


def read_from_file(filepath: str) -> str:
    """
    Reads the entire content of a file.

    Args:
        filepath: The path to the file to be read.

    Returns:
        The content of the file as a string.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"No such file: '{filepath}'")
    return path.read_text(encoding="utf-8")


def write_to_file(filepath: str, content: str) -> None:
    """
    Writes content to a file, creating parent directories if they don't exist.

    Args:
        filepath: The path to the file to be written.
        content: The string content to write to the file.
    """
    path = Path(filepath)
    # Ensure the parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
