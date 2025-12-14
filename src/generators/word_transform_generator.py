import re
from pathlib import Path
from typing import Generator

from cleanup import process_domain
from utils.io_utils import write_batches


class WordTransformGenerator:
    """
    A domain name generator that transforms words from a text file into valid domains
    by cleaning, normalizing, and appending TLDs.
    """

    # Lithuanian characters to Latin mapping
    LITHUANIAN_TO_LATIN = {
        'ą': 'a', 'č': 'c', 'ę': 'e', 'ė': 'e', 'į': 'i', 'š': 's', 'ų': 'u', 'ū': 'u', 'ž': 'z',
        'Ą': 'A', 'Č': 'C', 'Ę': 'E', 'Ė': 'E', 'Į': 'I', 'Š': 'S', 'Ų': 'U', 'Ū': 'U', 'Ž': 'Z',
    }

    def __init__(self, input_file: str, tld: str = 'lt'):
        """
        Initialize the word transform generator.

        Args:
            input_file: Path to input text file (one word per line)
            tld: Top-level domain to append (default: 'lt')
        """
        self.input_file = Path(input_file)
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        self.tld = tld.lstrip('.')  # Remove leading dot if present

    def clean_word(self, word: str) -> str:
        """
        Clean a word by removing non-alphanumeric characters except hyphens.

        Args:
            word: Raw word string

        Returns:
            Cleaned word string
        """
        # Remove all non-alphanumeric except hyphens
        return re.sub(r'[^a-zA-Z0-9-]', '', word)

    def normalize_lithuanian_chars(self, text: str) -> str:
        """
        Convert Lithuanian characters to their Latin equivalents.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        return ''.join(self.LITHUANIAN_TO_LATIN.get(char, char) for char in text)

    def transform_word(self, word: str) -> str:
        """
        Transform a single word into a domain.

        Args:
            word: Raw word from input file

        Returns:
            Transformed domain with TLD
        """
        # Convert to lowercase first
        lowercased = word.lower()
        # Normalize Lithuanian characters
        normalized = self.normalize_lithuanian_chars(lowercased)
        # Clean non-alphanumeric except hyphens (after normalization)
        cleaned = self.clean_word(normalized)
        # Form domain
        return f"{cleaned}.{self.tld}"

    def estimate_count(self) -> int:
        """
        Estimate total number of valid domains that will be generated.

        Returns:
            Estimated count based on input file line count
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                return sum(1 for line in f if line.strip())
        except Exception:
            return 0

    def generate(self) -> Generator[str, None, None]:
        """
        Generate transformed domains from input file.

        Yields:
            Valid domain names with TLD
        """
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if word:  # Skip empty lines
                        domain = self.transform_word(word)
                        cleaned, reason = process_domain(
                            domain,
                            target_tld=self.tld,
                            allow_other_tlds=True,
                            allow_subdomains=False,
                        )
                        if cleaned:
                            yield cleaned
        except Exception as e:
            raise RuntimeError(f"Error reading input file: {e}")

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