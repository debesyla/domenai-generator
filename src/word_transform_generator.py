import re
from pathlib import Path
from typing import Generator

from cleanup import process_domain
from io_utils import write_batches


class WordTransformGenerator:
    """
    A domain name generator that transforms words from a text file into valid domains
    by cleaning, normalizing, and appending TLDs.
    """

    # Diacritical marks to Latin mapping (European languages)
    DIACRITICS_TO_LATIN = {
        # Lithuanian
        'ą': 'a', 'č': 'c', 'ę': 'e', 'ė': 'e', 'į': 'i', 'š': 's', 'ų': 'u', 'ū': 'u', 'ž': 'z',
        'Ą': 'A', 'Č': 'C', 'Ę': 'E', 'Ė': 'E', 'Į': 'I', 'Š': 'S', 'Ų': 'U', 'Ū': 'U', 'Ž': 'Z',
        # German/Nordic
        'ä': 'a', 'ö': 'o', 'ü': 'u', 'ß': 'ss',
        'Ä': 'A', 'Ö': 'O', 'Ü': 'U',
        'å': 'a', 'Å': 'A',
        # French
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'É': 'E', 'È': 'E', 'Ê': 'E', 'Ë': 'E',
        'à': 'a', 'â': 'a', 'ã': 'a',
        'À': 'A', 'Â': 'A', 'Ã': 'A',
        'ô': 'o', 'õ': 'o',
        'Ô': 'O', 'Õ': 'O',
        'ù': 'u', 'û': 'u',
        'Ù': 'U', 'Û': 'U',
        'ç': 'c', 'Ç': 'C',
        # Spanish/Portuguese
        'á': 'a', 'ñ': 'n', 'Á': 'A', 'Ñ': 'N', 'ó': 'o', 'Ó': 'O',
        # Polish
        'ł': 'l', 'ć': 'c', 'ń': 'n', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ł': 'L', 'Ć': 'C', 'Ń': 'N', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z',
        # Czech/Slovak
        'ď': 'd', 'ě': 'e', 'ň': 'n', 'ř': 'r', 'ů': 'u',
        'Ď': 'D', 'Ě': 'E', 'Ň': 'N', 'Ř': 'R', 'Ů': 'U',
        # Romanian
        'ă': 'a', 'î': 'i', 'ţ': 't',
        'Ă': 'A', 'Î': 'I', 'Ţ': 'T',
        # Hungarian
        'ő': 'o', 'ű': 'u',
        'Ő': 'O', 'Ű': 'U',
        # Other common (Turkish, etc.)
        'ı': 'i', 'ğ': 'g', 'ş': 's', 'ú': 'u', 'ý': 'y',
        'Ğ': 'G', 'Ş': 'S', 'Ú': 'U', 'Ý': 'Y',
    }

    def __init__(self, input_file: str = None, tld: str = 'lt'):
        """
        Initialize the word transform generator.

        Args:
            input_file: Path to input text file (one word per line)
            tld: Top-level domain to append (default: 'lt')
        """
        if input_file is None:
            input_file = 'assets/input/input.txt'  # Default input file
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

    def normalize_diacritics(self, text: str) -> str:
        """
        Convert diacritical marks to their Latin equivalents.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        return ''.join(self.DIACRITICS_TO_LATIN.get(char, char) for char in text)

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
        # Normalize diacritical marks
        normalized = self.normalize_diacritics(lowercased)
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
        # Ensure uniqueness while preserving input order
        seen = set()
        try:
            with open(self.input_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip()
                    if not word:
                        continue
                    domain = self.transform_word(word)
                    cleaned, reason = process_domain(
                        domain,
                        target_tld=self.tld,
                        allow_other_tlds=True,
                        allow_subdomains=False,
                    )
                    if cleaned and cleaned not in seen:
                        seen.add(cleaned)
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
        estimated = self.estimate_count()
        return write_batches(
            self.generate(),
            filepath,
            batch_size=batch_size,
            progress_total=estimated if estimated > 0 else None,
        )