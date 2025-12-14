# Dago Domenai Generator

A simple toolkit for generating domain name lists using brute-force and word-transformation strategies.

## Features

- **Brute Force Generator**: Exhaustive combinations of characters within specified lengths.
- **Word Transform Generator**: Transform words from a file into domains (e.g., normalizing Lithuanian characters).
- **Cleanup Utility**: Tools to clean, validate, and filter domain lists.

## Requirements

- Python 3.8+

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dago-domenai-generator.git
cd dago-domenai-generator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Brute Force Generator

Generate all possible combinations:

```bash
python src/main.py brute \
  --min 2 \
  --max 4 \
  --charset alphanumeric \
  --output assets/output/brute_generated.txt
```

### Word Transform Generator

Transform words from a file to domains:

```bash
python src/main.py word_transform \
  --input assets/input/words.txt \
  --tld lt
```

### Cleanup Utility

Clean and normalize a domain list:

```bash
python src/main.py cleanup \
  --input assets/input/raw_domains.txt \
  --output assets/output/clean_domains.txt
```

## Project Structure

```
dago-domenai-generator/
├── README.md
├── requirements.txt
├── assets/
│   ├── input/
│   └── output/
├── src/
│   ├── main.py
│   ├── brute_generator.py
│   ├── word_transform_generator.py
│   ├── cleanup.py
│   └── io_utils.py
└── tests/
```

## AI notice

LLM engines were used to generate, edit parts of the code. Most of it, actually. So keep that in mind and so you are free to do anything with this tool. Have fun!