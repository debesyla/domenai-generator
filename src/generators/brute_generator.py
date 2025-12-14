import itertools
from typing import Generator, Optional
from pathlib import Path

from utils.io_utils import write_batches


class BruteForceGenerator:
    """
    A systematic domain name generator that produces all possible combinations
    of characters for a given length range with DNS validation.
    """

    CHARACTER_SETS = {
        'numbers': '0123456789',
        'letters': 'abcdefghijklmnopqrstuvwxyz',
        'alphanumeric': 'abcdefghijklmnopqrstuvwxyz0123456789',
    }

    def __init__(self, char_type: str = 'alphanumeric', min_len: int = 2,
                 max_len: int = 4, hyphen_mode: str = 'with', tld: str = 'lt'):
        """
        Initialize the brute force generator.

        Args:
            char_type: Character set type ('numbers', 'letters', 'alphanumeric')
            min_len: Minimum domain length (excluding TLD)
            max_len: Maximum domain length (excluding TLD)
            hyphen_mode: Hyphen handling ('with', 'without', 'only')
            tld: Top-level domain (e.g., 'com', 'lt')
        """
        if char_type not in self.CHARACTER_SETS:
            raise ValueError(f"Invalid char_type. Must be one of: {list(self.CHARACTER_SETS.keys())}")

        if hyphen_mode not in ['with', 'without', 'only']:
            raise ValueError("hyphen_mode must be 'with', 'without', or 'only'")

        if min_len < 1 or max_len < min_len or max_len > 63:
            raise ValueError("Invalid length range. Must have 1 <= min_len <= max_len <= 63")

        self.char_type = char_type
        self.min_len = min_len
        self.max_len = max_len
        self.hyphen_mode = hyphen_mode
        self.tld = tld
        self.charset = self.get_character_set()

    def get_character_set(self) -> str:
        """
        Get the character set based on type and hyphen mode.

        Returns:
            String of valid characters for domain generation
        """
        base_chars = self.CHARACTER_SETS[self.char_type]

        if self.hyphen_mode in ['with', 'only']:
            return base_chars + '-'
        return base_chars

    def validate_domain(self, domain: str) -> bool:
        """
        Validate domain against DNS naming rules.

        Args:
            domain: Domain name to validate (without TLD)

        Returns:
            True if domain is valid, False otherwise
        """
        # Cannot start or end with hyphen
        if domain.startswith('-') or domain.endswith('-'):
            return False

        # Cannot have consecutive hyphens
        if '--' in domain:
            return False

        # Check hyphen mode requirements
        if self.hyphen_mode == 'only' and '-' not in domain:
            return False

        # Length check (though this should be handled by generation params)
        if len(domain) < self.min_len or len(domain) > self.max_len:
            return False

        return True

    def estimate_count(self) -> int:
        """
        Estimate total number of valid domains before generation.

        Returns:
            Estimated count of domains that will be generated
        """
        charset_size = len(self.charset)
        total = 0

        for length in range(self.min_len, self.max_len + 1):
            total += charset_size ** length

        # Apply rough validation filter based on hyphen mode
        if self.hyphen_mode == 'with':
            # Account for domains that start/end with hyphens or have consecutive hyphens
            total = int(total * 0.90)
        elif self.hyphen_mode == 'only':
            # Only ~30% will have hyphens after filtering invalid positions
            total = int(total * 0.30)

        return total

    def generate(self) -> Generator[str, None, None]:
        """
        Generate all valid domain combinations.

        Yields:
            Domain names with TLD (e.g., 'abc.lt')
        """
        for length in range(self.min_len, self.max_len + 1):
            for combo in itertools.product(self.charset, repeat=length):
                domain = ''.join(combo)
                if self.validate_domain(domain):
                    yield f"{domain}.{self.tld}"

    def generate_to_file(self, filepath: str, batch_size: int = 10000) -> int:
        """
        Generate domains and write to file in batches.

        Args:
            filepath: Output file path
            batch_size: Number of domains to write per batch

        Returns:
            Total number of domains written
        """
        return write_batches(self.generate(), filepath, batch_size=batch_size)