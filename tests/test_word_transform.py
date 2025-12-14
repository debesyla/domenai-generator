import unittest
import tempfile
import os
from pathlib import Path
from src.word_transform_generator import WordTransformGenerator


class TestWordTransformGenerator(unittest.TestCase):
    """Test cases for WordTransformGenerator."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary input file for testing
        self.temp_input = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.temp_input.write("hello\nworld\nKaunas\nVilnius\nęžuolas\nšuo\n")
        self.temp_input.close()

    def tearDown(self):
        """Clean up test fixtures."""
        os.unlink(self.temp_input.name)

    def test_init_valid_params(self):
        """Test initialization with valid parameters."""
        generator = WordTransformGenerator(
            input_file=self.temp_input.name,
            tld='lt'
        )
        self.assertEqual(generator.input_file, Path(self.temp_input.name))
        self.assertEqual(generator.tld, 'lt')

    def test_init_file_not_found(self):
        """Test initialization with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            WordTransformGenerator(input_file='nonexistent.txt')

    def test_clean_word(self):
        """Test word cleaning functionality."""
        generator = WordTransformGenerator(input_file=self.temp_input.name)

        # Test basic cleaning
        self.assertEqual(generator.clean_word("hello.world"), "helloworld")
        self.assertEqual(generator.clean_word("hello world"), "helloworld")
        self.assertEqual(generator.clean_word("hello-world"), "hello-world")
        self.assertEqual(generator.clean_word("hello123!@#"), "hello123")

    def test_normalize_lithuanian_chars(self):
        """Test Lithuanian character normalization."""
        generator = WordTransformGenerator(input_file=self.temp_input.name)

        # Test Lithuanian characters
        self.assertEqual(generator.normalize_lithuanian_chars("ęžuolas"), "ezuolas")
        self.assertEqual(generator.normalize_lithuanian_chars("šuo"), "suo")
        self.assertEqual(generator.normalize_lithuanian_chars("ąčęėįšųūž"), "aceeisuuz")

        # Test uppercase
        self.assertEqual(generator.normalize_lithuanian_chars("ĄČĘĖĮŠŲŪŽ"), "ACEEISUUZ")

        # Test mixed
        self.assertEqual(generator.normalize_lithuanian_chars("Kaunas"), "Kaunas")

    def test_transform_word(self):
        """Test complete word transformation."""
        generator = WordTransformGenerator(input_file=self.temp_input.name, tld='lt')

        # Test basic transformation
        self.assertEqual(generator.transform_word("Hello.World"), "helloworld.lt")
        self.assertEqual(generator.transform_word("Ęžuolas"), "ezuolas.lt")
        self.assertEqual(generator.transform_word("KAUNAS"), "kaunas.lt")

    def test_validate_domain_valid(self):
        """Test domain validation with valid domains."""
        generator = WordTransformGenerator(input_file=self.temp_input.name)

        self.assertTrue(generator.validate_domain('hello.lt'))
        self.assertTrue(generator.validate_domain('world.lt'))
        self.assertTrue(generator.validate_domain('test-domain.lt'))
        self.assertTrue(generator.validate_domain('a.lt'))

    def test_validate_domain_invalid_hyphen_start(self):
        """Test domain validation rejects domains starting with hyphen."""
        generator = WordTransformGenerator(input_file=self.temp_input.name)
        self.assertFalse(generator.validate_domain('-hello.lt'))

    def test_validate_domain_invalid_hyphen_end(self):
        """Test domain validation rejects domains ending with hyphen."""
        generator = WordTransformGenerator(input_file=self.temp_input.name)
        self.assertFalse(generator.validate_domain('hello-.lt'))

    def test_validate_domain_invalid_consecutive_hyphens(self):
        """Test domain validation rejects domains with consecutive hyphens."""
        generator = WordTransformGenerator(input_file=self.temp_input.name)
        self.assertFalse(generator.validate_domain('hel--lo.lt'))

    def test_validate_domain_length(self):
        """Test domain validation with length constraints."""
        generator = WordTransformGenerator(input_file=self.temp_input.name)

        # Empty label
        self.assertFalse(generator.validate_domain('.lt'))

        # Too long label (over 63 chars)
        long_label = 'a' * 64
        self.assertFalse(generator.validate_domain(f'{long_label}.lt'))

        # Valid lengths
        self.assertTrue(generator.validate_domain('a.lt'))
        self.assertTrue(generator.validate_domain('a' * 63 + '.lt'))

    def test_validate_domain_no_alphanumeric(self):
        """Test domain validation rejects domains with no alphanumeric characters."""
        generator = WordTransformGenerator(input_file=self.temp_input.name)
        self.assertFalse(generator.validate_domain('---.lt'))

    def test_estimate_count(self):
        """Test count estimation."""
        generator = WordTransformGenerator(input_file=self.temp_input.name)
        # Input file has 6 lines (some may be empty after strip)
        estimated = generator.estimate_count()
        self.assertEqual(estimated, 6)

    def test_generate(self):
        """Test domain generation."""
        generator = WordTransformGenerator(input_file=self.temp_input.name, tld='lt')
        domains = list(generator.generate())

        # Should generate domains for each non-empty line
        expected_domains = [
            'hello.lt',
            'world.lt',
            'kaunas.lt',
            'vilnius.lt',
            'ezuolas.lt',
            'suo.lt'
        ]
        self.assertEqual(domains, expected_domains)

    def test_generate_empty_file(self):
        """Test generation with empty input file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            empty_file = f.name

        try:
            generator = WordTransformGenerator(input_file=empty_file)
            domains = list(generator.generate())
            self.assertEqual(domains, [])
        finally:
            os.unlink(empty_file)

    def test_generate_to_file(self):
        """Test file output functionality."""
        generator = WordTransformGenerator(input_file=self.temp_input.name, tld='test')

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_file = f.name

        try:
            count = generator.generate_to_file(temp_file)
            self.assertEqual(count, 6)

            # Verify file contents
            with open(temp_file, 'r') as f:
                lines = f.read().strip().split('\n')
                expected = [
                    'hello.test',
                    'world.test',
                    'kaunas.test',
                    'vilnius.test',
                    'ezuolas.test',
                    'suo.test'
                ]
                self.assertEqual(lines, expected)
        finally:
            os.unlink(temp_file)

    def test_tld_handling(self):
        """Test TLD handling with and without leading dot."""
        # With leading dot
        gen1 = WordTransformGenerator(input_file=self.temp_input.name, tld='.com')
        self.assertEqual(gen1.tld, 'com')

        # Without leading dot
        gen2 = WordTransformGenerator(input_file=self.temp_input.name, tld='com')
        self.assertEqual(gen2.tld, 'com')

        # Test generation
        domains1 = list(gen1.generate())
        domains2 = list(gen2.generate())
        self.assertEqual(domains1, domains2)


if __name__ == '__main__':
    unittest.main()