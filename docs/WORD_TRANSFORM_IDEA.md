# Word Transform Domain Generator

## Overview
This generator takes a text file containing one word per line and transforms each word into a potential .lt domain by cleaning non-alphanumeric characters, normalizing Lithuanian characters to Latin equivalents, and appending the .lt TLD.

## Goals

### Primary Objectives
1. **Input Processing**: Read words from a text file (one word per line)
2. **Character Cleaning**: Remove dots, spaces, and other non-alphanumeric characters except hyphens
3. **Case Normalization**: Convert all characters to lowercase
4. **Lithuanian Character Normalization**: Convert Lithuanian-specific characters (ė, ę, etc.) to their Latin equivalents
5. **Domain Formation**: Append '.lt' to each cleaned word
6. **Output Generation**: Write resulting domains to a .txt file

### Secondary Objectives
- Memory-efficient processing using generators
- Progress tracking for large input files
- Validation of resulting domains against DNS rules
- Support for custom TLDs (not just .lt)

## Technical Solution

### Core Algorithm

```python
def transform_word_to_domain(word, tld='.lt'):
    """Transform a single word into a domain"""
    # Clean non-alphanumeric except hyphens
    cleaned = re.sub(r'[^a-zA-Z0-9-]', '', word)
    # Convert to lowercase
    lowercased = cleaned.lower()
    # Normalize Lithuanian characters
    normalized = normalize_lithuanian_chars(lowercased)
    # Form domain
    domain = normalized + tld
    return domain
```

def generate_domains(input_file, output_file, tld='.lt'):
    """Generate domains from word list"""
    with open(input_file, 'r', encoding='utf-8') as f_in:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                word = line.strip()
                if word:
                    domain = transform_word_to_domain(word, tld)
                    if is_valid_domain(domain):
                        f_out.write(domain + '\n')
```

### Lithuanian Character Mapping

```python
LITHUANIAN_TO_LATIN = {
    'ą': 'a',
    'č': 'c',
    'ę': 'e',
    'ė': 'e',
    'į': 'i',
    'š': 's',
    'ų': 'u',
    'ū': 'u',
    'ž': 'z',
    # Uppercase versions
    'Ą': 'A',
    'Č': 'C',
    'Ę': 'E',
    'Ė': 'E',
    'Į': 'I',
    'Š': 'S',
    'Ų': 'U',
    'Ū': 'U',
    'Ž': 'Z',
}
```

### Validation Rules
- Domain label must be 1-63 characters
- Cannot start or end with hyphen
- No consecutive hyphens
- Only alphanumeric and hyphens allowed

## Implementation Notes
- Use UTF-8 encoding for input/output
- Handle empty lines gracefully
- Provide count estimation based on input file size
- Support command-line parameters for input file, output file, and TLD