from pathlib import Path
from typing import Iterable


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
