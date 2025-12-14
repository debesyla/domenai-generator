"""
Tests for MarkovGenerator
"""
import pytest
from pathlib import Path
import tempfile
import os

from markov_generator import MarkovGenerator


@pytest.fixture
def sample_corpus_file():
    """Create a temporary corpus file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        # Write some sample domains
        f.write("test.lt\n")
        f.write("demo.lt\n")
        f.write("sample.lt\n")
        f.write("example.lt\n")
        f.write("domain.lt\n")
        f.write("testing.lt\n")
        f.write("demonstration.lt\n")
        f.write("alpha\n")
        f.write("beta\n")
        f.write("gamma\n")
        f.write("delta\n")
        f.write("epsilon\n")
        f.write("data\n")
        f.write("code\n")
        f.write("test123\n")
        f.write("abc-def\n")
        filename = f.name

    yield filename

    # Cleanup
    os.unlink(filename)


def test_markov_generator_initialization(sample_corpus_file):
    """Test MarkovGenerator initialization."""
    generator = MarkovGenerator(
        input_file=sample_corpus_file,
        order=2,
        min_len=3,
        max_len=6,
        count=10,
        tld='lt',
        min_frequency=1
    )

    assert generator.order == 2
    assert generator.min_len == 3
    assert generator.max_len == 6
    assert generator.count == 10
    assert generator.tld == 'lt'
    assert len(generator.training_set) > 0
    assert len(generator.transitions) > 0


def test_markov_generator_invalid_params():
    """Test MarkovGenerator with invalid parameters."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test\n")
        temp_file = f.name

    try:
        # Invalid order
        with pytest.raises(ValueError, match="Order must be at least 1"):
            MarkovGenerator(temp_file, order=0, count=10)

        # Invalid length range
        with pytest.raises(ValueError, match="Invalid length range"):
            MarkovGenerator(temp_file, order=2, min_len=10, max_len=5, count=10)

        # Invalid count
        with pytest.raises(ValueError, match="Count must be at least 1"):
            MarkovGenerator(temp_file, order=2, count=0)
    finally:
        os.unlink(temp_file)


def test_markov_generator_missing_file():
    """Test MarkovGenerator with non-existent input file."""
    with pytest.raises(FileNotFoundError):
        MarkovGenerator(
            input_file='nonexistent_file.txt',
            order=2,
            count=10
        )


def test_normalize_input(sample_corpus_file):
    """Test input normalization."""
    generator = MarkovGenerator(sample_corpus_file, order=2, count=10)

    # Test TLD removal
    assert generator._normalize_input("test.lt") == "test"
    assert generator._normalize_input("TEST.COM") == "test"

    # Test lowercase
    assert generator._normalize_input("UPPERCASE") == "uppercase"

    # Test hyphen handling
    assert generator._normalize_input("test-domain") == "test-domain"
    assert generator._normalize_input("-leading") == "leading"
    assert generator._normalize_input("trailing-") == "trailing"

    # Test invalid characters removal
    assert generator._normalize_input("test@#$domain") == "testdomain"


def test_generate_basic(sample_corpus_file):
    """Test basic domain generation."""
    generator = MarkovGenerator(
        input_file=sample_corpus_file,
        order=2,
        min_len=3,
        max_len=6,
        count=5,
        tld='',  # No TLD for easier testing
        min_frequency=1
    )

    domains = list(generator.generate())

    # Should generate requested count (or close to it)
    assert len(domains) > 0
    assert len(domains) <= 5

    # All should be within length range
    for domain in domains:
        assert 3 <= len(domain) <= 6

    # All should be unique
    assert len(domains) == len(set(domains))

    # None should be in training set
    for domain in domains:
        assert domain not in generator.training_set


def test_generate_to_file(sample_corpus_file):
    """Test generating domains to file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / 'output.txt'

        generator = MarkovGenerator(
            input_file=sample_corpus_file,
            order=2,
            min_len=3,
            max_len=6,
            count=10,
            tld='lt',
            min_frequency=1
        )

        count = generator.generate_to_file(str(output_file))

        # Should write some domains
        assert count > 0
        assert count <= 10

        # File should exist and have content
        assert output_file.exists()
        with open(output_file, 'r') as f:
            lines = f.readlines()

        assert len(lines) == count

        # All lines should end with .lt
        for line in lines:
            assert line.strip().endswith('.lt')


def test_estimate_count(sample_corpus_file):
    """Test count estimation."""
    generator = MarkovGenerator(
        input_file=sample_corpus_file,
        order=2,
        min_len=3,
        max_len=6,
        count=100,
        tld='lt'
    )

    estimate = generator.estimate_count()
    assert estimate == 100  # Markov returns target count


def test_weighted_choice():
    """Test weighted random choice."""
    from collections import Counter

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test\n")
        temp_file = f.name

    try:
        generator = MarkovGenerator(temp_file, order=2, count=10)

        # Test with valid counter
        counter = Counter({'a': 10, 'b': 5, 'c': 1})
        choices = [generator._weighted_choice(counter) for _ in range(100)]

        # All choices should be valid
        assert all(c in ['a', 'b', 'c'] for c in choices)

        # 'a' should appear most frequently (though probabilistic)
        assert choices.count('a') > choices.count('c')

        # Test with empty counter
        assert generator._weighted_choice(Counter()) is None
    finally:
        os.unlink(temp_file)


def test_dns_validation(sample_corpus_file):
    """Test that generated domains follow DNS rules."""
    generator = MarkovGenerator(
        input_file=sample_corpus_file,
        order=2,
        min_len=3,
        max_len=8,
        count=20,
        tld='',
        min_frequency=1
    )

    domains = list(generator.generate())

    for domain in domains:
        # Should not start or end with hyphen
        assert not domain.startswith('-')
        assert not domain.endswith('-')

        # Should not have consecutive hyphens
        assert '--' not in domain

        # Should only contain valid characters
        assert all(c.isalnum() or c == '-' for c in domain)


def test_different_orders(sample_corpus_file):
    """Test generation with different n-gram orders."""
    for order in [1, 2, 3, 4]:
        generator = MarkovGenerator(
            input_file=sample_corpus_file,
            order=order,
            min_len=3,
            max_len=6,
            count=5,
            tld='',
            min_frequency=1
        )

        domains = list(generator.generate())
        assert len(domains) > 0

        # Higher orders should have more states
        if order > 1:
            assert len(generator.transitions) > 0
