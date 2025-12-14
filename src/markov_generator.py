"""
Markov chain-based domain/word generator using n-gram transitions.

Trains on corpus of domains/words (one per line) and generates new combinations
following learned character transition probabilities.
"""
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Generator, Set, Dict, List

from io_utils import write_batches


class MarkovGenerator:
    """
    A Markov chain generator that learns character sequences from input
    and produces new domain/word candidates based on transition probabilities.
    """

    def __init__(
        self,
        input_file: str,
        order: int = 3,
        min_len: int = 2,
        max_len: int = 8,
        count: int = 10000,
        tld: str = 'lt',
        min_frequency: int = 2
    ):
        """
        Initialize the Markov generator and train on input corpus.

        Args:
            input_file: Path to input file (one word/domain per line)
            order: N-gram order (e.g., 3 for trigrams)
            min_len: Minimum generated length
            max_len: Maximum generated length
            count: Number of domains to generate
            tld: Top-level domain to append
            min_frequency: Minimum n-gram frequency to include in model
        """
        if order < 1:
            raise ValueError("Order must be at least 1")
        if min_len < 1 or max_len < min_len or max_len > 63:
            raise ValueError("Invalid length range. Must have 1 <= min_len <= max_len <= 63")
        if count < 1:
            raise ValueError("Count must be at least 1")

        self.input_file = Path(input_file)
        self.order = order
        self.min_len = min_len
        self.max_len = max_len
        self.count = count
        self.tld = tld
        self.min_frequency = min_frequency

        # Model storage
        self.transitions: Dict[str, Counter] = defaultdict(Counter)
        self.start_states: Counter = Counter()
        self.training_set: Set[str] = set()

        # Train on input
        self._train()

    def _normalize_input(self, line: str) -> str:
        """
        Normalize input line to clean domain/word.

        Args:
            line: Raw input line

        Returns:
            Cleaned string (lowercase, no TLD, valid chars only)
        """
        text = line.strip().lower()

        # Remove common TLDs if present
        for tld in ['.lt', '.com', '.net', '.org', '.io', '.co']:
            if text.endswith(tld):
                text = text[:-len(tld)]
                break

        # Keep only valid DNS characters: a-z, 0-9, hyphen
        text = ''.join(c for c in text if c.isalnum() or c == '-')

        # Remove leading/trailing hyphens
        text = text.strip('-')

        return text

    def _train(self):
        """
        Train the Markov model on input corpus.
        Extracts n-gram transitions and starting states.
        """
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")

        print(f"Training Markov model (order={self.order}) on {self.input_file}...")

        processed = 0
        with open(self.input_file, 'r', encoding='utf-8') as f:
            for line in f:
                text = self._normalize_input(line)

                # Skip invalid entries
                if len(text) < self.order or len(text) > 63:
                    continue

                # Add to training set for deduplication
                self.training_set.add(text)

                # Add boundary markers
                text = '^' * self.order + text + '$'

                # Extract start state (first n characters after boundary)
                start_state = text[:self.order]
                self.start_states[start_state] += 1

                # Extract transitions (n-gram -> next char)
                for i in range(len(text) - self.order):
                    state = text[i:i + self.order]
                    next_char = text[i + self.order]
                    self.transitions[state][next_char] += 1

                processed += 1
                if processed % 10000 == 0:
                    print(f"  Processed {processed:,} entries...")

        # Filter by minimum frequency
        self._filter_by_frequency()

        print(f"Training complete:")
        print(f"  Processed: {processed:,} entries")
        print(f"  Unique training samples: {len(self.training_set):,}")
        print(f"  States in model: {len(self.transitions):,}")
        print(f"  Start states: {len(self.start_states):,}")

    def _filter_by_frequency(self):
        """Remove low-frequency transitions from model."""
        if self.min_frequency <= 1:
            return

        # Filter transitions
        filtered_transitions = defaultdict(Counter)
        for state, counter in self.transitions.items():
            for next_char, freq in counter.items():
                if freq >= self.min_frequency:
                    filtered_transitions[state][next_char] = freq

        # Filter start states
        self.start_states = Counter({
            state: count for state, count in self.start_states.items()
            if count >= self.min_frequency
        })

        original_count = len(self.transitions)
        self.transitions = filtered_transitions
        print(f"  Filtered states: {original_count:,} -> {len(self.transitions):,}")

    def _weighted_choice(self, counter: Counter) -> str:
        """
        Choose random element from counter based on frequency weights.

        Args:
            counter: Counter with elements and frequencies

        Returns:
            Randomly selected element
        """
        if not counter:
            return None

        elements = list(counter.keys())
        weights = list(counter.values())
        return random.choices(elements, weights=weights, k=1)[0]

    def _generate_one(self) -> str:
        """
        Generate a single domain using the Markov model.

        Returns:
            Generated domain string (without TLD), or None if generation fails
        """
        if not self.start_states:
            return None

        # Choose starting state
        state = self._weighted_choice(self.start_states)
        result = state.replace('^', '')  # Remove boundary markers

        max_attempts = self.max_len * 3  # Prevent infinite loops
        attempts = 0

        while attempts < max_attempts:
            attempts += 1

            # Get next character from current state
            if state not in self.transitions:
                break

            next_char = self._weighted_choice(self.transitions[state])
            if not next_char:
                break

            # End of sequence marker
            if next_char == '$':
                if len(result) >= self.min_len:
                    break
                else:
                    # Too short, try to continue
                    continue

            result += next_char

            # Max length reached
            if len(result) >= self.max_len:
                break

            # Update state (slide window)
            state = state[1:] + next_char

        # Final validation
        if len(result) < self.min_len or len(result) > self.max_len:
            return None

        # Basic DNS validation
        if result.startswith('-') or result.endswith('-') or '--' in result:
            return None

        return result

    def generate(self) -> Generator[str, None, None]:
        """
        Generate domain names using the Markov model.

        Yields:
            Generated domain names (without TLD)
        """
        generated = set()
        attempts = 0
        max_attempts = self.count * 100  # Allow retries for duplicates

        while len(generated) < self.count and attempts < max_attempts:
            attempts += 1
            domain = self._generate_one()

            if domain and domain not in self.training_set and domain not in generated:
                generated.add(domain)
                yield domain

            if attempts % 10000 == 0:
                print(f"  Generated {len(generated):,}/{self.count:,} unique domains (attempts: {attempts:,})...")

    def generate_to_file(self, filepath: str) -> int:
        """
        Generate domains and write to file.

        Args:
            filepath: Output file path

        Returns:
            Number of domains written
        """
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"Generating {self.count:,} domains...")

        # Add TLD if specified
        domains = self.generate()
        if self.tld:
            domains = (f"{d}.{self.tld}" for d in domains)

        count = write_batches(
            domains,
            filepath,
            batch_size=10000,
            progress_total=self.count,
            progress_every=10000
        )

        return count

    def estimate_count(self) -> int:
        """
        Return the target count (Markov doesn't have deterministic estimate).

        Returns:
            Target generation count
        """
        return self.count
