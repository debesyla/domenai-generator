from typing import Generator, Protocol


class GeneratorProtocol(Protocol):
    """
    Contract for all domain generators.

    Implementations must be memory-efficient and yield one domain at a time.
    """

    def generate(self) -> Generator[str, None, None]:
        """Yield domains one by one (including TLD)."""
        ...

    def estimate_count(self) -> int:
        """Return an estimated count of items to be generated."""
        ...

    def generate_to_file(self, filepath: str, batch_size: int = 10000) -> int:
        """Write generated domains to file in batches; return count written."""
        ...
