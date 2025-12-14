from pathlib import Path
from typing import Iterable


def make_output_path(prefix: str, **params) -> str:
    """
    Build a consistent output path in assets/output based on a prefix and parameters.

    Example: make_output_path('brute', charset='alphanumeric', rng='2-4', hyphen='with', tld='lt')
    -> 'assets/output/brute_alphanumeric_2-4_with_lt.txt'
    """
    parts = [prefix]
    for key, val in params.items():
        if val is None:
            continue
        parts.append(str(val))
    filename = '_'.join(parts) + '.txt'
    return str(Path('assets') / 'output' / filename)


def write_batches(iterable: Iterable[str], filepath: str, batch_size: int = 10000) -> int:
    """
    Write items from an iterable to a file in batches (one per line).

    Args:
        iterable: Iterable of strings to write.
        filepath: Destination file path.
        batch_size: Number of lines per batch write.

    Returns:
        Total number of items written.
    """
    count = 0
    batch = []

    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for item in iterable:
            batch.append(item)
            count += 1
            if len(batch) >= batch_size:
                f.write('\n'.join(batch) + '\n')
                batch = []

        if batch:
            f.write('\n'.join(batch) + '\n')

    return count
