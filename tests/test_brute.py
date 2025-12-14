import unittest
import tempfile
import os
from src.brute_generator import BruteForceGenerator


class TestBruteForceGenerator(unittest.TestCase):
    """Test cases for BruteForceGenerator."""

    def test_init_valid_params(self):
        """Test initialization with valid parameters."""
        generator = BruteForceGenerator(
            char_type='alphanumeric',
            min_len=2,
            max_len=4,
            hyphen_mode='with',
            tld='lt'
        )
        self.assertEqual(generator.char_type, 'alphanumeric')
        self.assertEqual(generator.min_len, 2)
        self.assertEqual(generator.max_len, 4)
        self.assertEqual(generator.hyphen_mode, 'with')
        self.assertEqual(generator.tld, 'lt')

    def test_init_invalid_char_type(self):
        """Test initialization with invalid character type."""
        with self.assertRaises(ValueError):
            BruteForceGenerator(char_type='invalid')

    def test_init_invalid_hyphen_mode(self):
        """Test initialization with invalid hyphen mode."""
        with self.assertRaises(ValueError):
            BruteForceGenerator(hyphen_mode='invalid')

    def test_init_invalid_lengths(self):
        """Test initialization with invalid length parameters."""
        with self.assertRaises(ValueError):
            BruteForceGenerator(min_len=0, max_len=4)

        with self.assertRaises(ValueError):
            BruteForceGenerator(min_len=5, max_len=3)

        with self.assertRaises(ValueError):
            BruteForceGenerator(min_len=1, max_len=64)

    def test_get_character_set_numbers(self):
        """Test character set generation for numbers."""
        generator = BruteForceGenerator(char_type='numbers', hyphen_mode='without')
        self.assertEqual(generator.get_character_set(), '0123456789')

    def test_get_character_set_letters(self):
        """Test character set generation for letters."""
        generator = BruteForceGenerator(char_type='letters', hyphen_mode='without')
        self.assertEqual(generator.get_character_set(), 'abcdefghijklmnopqrstuvwxyz')

    def test_get_character_set_alphanumeric(self):
        """Test character set generation for alphanumeric."""
        generator = BruteForceGenerator(char_type='alphanumeric', hyphen_mode='without')
        expected = 'abcdefghijklmnopqrstuvwxyz0123456789'
        self.assertEqual(generator.get_character_set(), expected)

    def test_get_character_set_with_hyphens(self):
        """Test character set generation with hyphens."""
        generator = BruteForceGenerator(char_type='letters', hyphen_mode='with')
        self.assertEqual(generator.get_character_set(), 'abcdefghijklmnopqrstuvwxyz-')

    def test_validate_domain_valid(self):
        """Test domain validation with valid domains."""
        generator = BruteForceGenerator(min_len=2, max_len=4, hyphen_mode='with')

        self.assertTrue(generator.validate_domain('ab'))
        self.assertTrue(generator.validate_domain('abc'))
        self.assertTrue(generator.validate_domain('a-b'))
        self.assertTrue(generator.validate_domain('12'))

    def test_validate_domain_invalid_hyphen_start(self):
        """Test domain validation rejects domains starting with hyphen."""
        generator = BruteForceGenerator(hyphen_mode='with')
        self.assertFalse(generator.validate_domain('-ab'))

    def test_validate_domain_invalid_hyphen_end(self):
        """Test domain validation rejects domains ending with hyphen."""
        generator = BruteForceGenerator(hyphen_mode='with')
        self.assertFalse(generator.validate_domain('ab-'))

    def test_validate_domain_invalid_consecutive_hyphens(self):
        """Test domain validation rejects domains with consecutive hyphens."""
        generator = BruteForceGenerator(hyphen_mode='with')
        self.assertFalse(generator.validate_domain('a--b'))

    def test_validate_domain_hyphen_only_mode(self):
        """Test domain validation in hyphen-only mode."""
        generator = BruteForceGenerator(hyphen_mode='only')
        self.assertTrue(generator.validate_domain('a-b'))
        self.assertFalse(generator.validate_domain('ab'))

    def test_validate_domain_length(self):
        """Test domain validation with length constraints."""
        generator = BruteForceGenerator(min_len=2, max_len=3)
        self.assertFalse(generator.validate_domain('a'))  # too short
        self.assertFalse(generator.validate_domain('abcd'))  # too long
        self.assertTrue(generator.validate_domain('ab'))
        self.assertTrue(generator.validate_domain('abc'))

    def test_estimate_count_numbers(self):
        """Test count estimation for numbers."""
        generator = BruteForceGenerator(
            char_type='numbers',
            min_len=1,
            max_len=2,
            hyphen_mode='without'
        )
        # 10^1 + 10^2 = 10 + 100 = 110, no filter for 'without' mode
        estimated = generator.estimate_count()
        self.assertEqual(estimated, 110)

    def test_estimate_count_with_hyphens(self):
        """Test count estimation with hyphens."""
        generator = BruteForceGenerator(
            char_type='numbers',
            min_len=1,
            max_len=1,
            hyphen_mode='with'
        )
        # 11^1 = 11, then * 0.90 = 9.9 -> 9
        estimated = generator.estimate_count()
        self.assertEqual(estimated, 9)

    def test_generate_small_set(self):
        """Test domain generation with small set."""
        generator = BruteForceGenerator(
            char_type='numbers',
            min_len=1,
            max_len=1,
            hyphen_mode='without',
            tld='lt'
        )
        domains = list(generator.generate())
        expected = [f"{i}.lt" for i in '0123456789']
        self.assertEqual(domains, expected)

    def test_generate_with_hyphens(self):
        """Test domain generation with hyphens."""
        generator = BruteForceGenerator(
            char_type='letters',
            min_len=2,
            max_len=2,
            hyphen_mode='only',
            tld='lt'
        )
        domains = list(generator.generate())
        # Should only include domains with hyphens
        self.assertTrue(all('-' in domain for domain in domains))
        self.assertTrue(all(domain.endswith('.lt') for domain in domains))

    def test_generate_to_file(self):
        """Test file output functionality."""
        generator = BruteForceGenerator(
            char_type='numbers',
            min_len=1,
            max_len=1,
            hyphen_mode='without',
            tld='test'
        )

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            temp_file = f.name

        try:
            count = generator.generate_to_file(temp_file)
            self.assertEqual(count, 10)

            # Verify file contents
            with open(temp_file, 'r') as f:
                lines = f.read().strip().split('\n')
                expected = [f"{i}.test" for i in '0123456789']
                self.assertEqual(lines, expected)
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    unittest.main()