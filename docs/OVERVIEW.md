## 🧩 **Project Overview**

**Goal:**
A repository that contains **multiple domain generation tools** — each generating domain name lists in different ways (e.g. brute-force, Markov-based, dictionary-based).
Each generator outputs `.txt` files that can be later consumed by external analysis tools (like WHOIS checkers, availability scanners, etc).

---

## 🗂️ **Folder Structure**

```
domain-generators/
├── README.md
├── requirements.txt
├── .gitignore
│
├── /docs/
│   ├── overview.md
│   ├── markov.md
│   ├── brute.md
│   ├── word_transform.md
│   └── roadmap.md
│
├── /assets/
│   ├── input/
│   │   ├── real_domains.txt        # 145k domain corpus
│   │   └── custom_dict.txt
│   └── output/
│       ├── markov_generated.txt
│       ├── brute_2char.txt
│       └── sample_output.txt
│
├── /src/
│   ├── __init__.py
│   │
│   ├── main.py                     # CLI entry point (select generator)
│   │
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── markov_generator.py     # Markov-based name generation
│   │   ├── brute_generator.py      # All combinations of given charset
│   │   ├── word_transform_generator.py  # Transform words to domains
│   │   ├── pattern_generator.py    # Generate via regex-like patterns
│   │   └── random_generator.py     # Pure random combinations
│   │
│   ├── utils/
│   │   ├── io_utils.py             # read/write helpers
│   │   ├── markov_utils.py         # markov chain training / sampling
│   │   └── progress_utils.py       # pretty console progress, ETA
│
└── /tests/
    ├── test_markov.py
    ├── test_brute.py
    └── test_io.py
```

---

## ⚙️ **Implementation Plan**

### **1. Base Infrastructure**

* `io_utils.py`:
  Handle reading/writing `.txt` domain lists (e.g. batching outputs to avoid memory overflow).
* `main.py`:
  Simple CLI selector:

  ```bash
  python3 src/main.py markov
  python3 src/main.py brute --length 2
  ```

  or even:

  ```bash
  python3 src/main.py all
  ```

### **2. Brute-force Generator**

* Generate all combinations of `[a-z0-9]` for a given length.
* Save to `/assets/output/brute_*.txt`.

Example usage:

```bash
python3 src/main.py brute --min 2 --max 4
```

---

### **3. Markov Generator**

* Train on your real domain corpus (`/assets/input/real_domains.txt`).
* Allow adjustable Markov order (2, 3, 4).
* Generate a set number of new domains.

Example usage:

```bash
python3 src/main.py markov --order 3 --count 10000
```

---

### **4. Word Transform Generator**

* Read words from a text file (one word per line)
* Clean non-alphanumeric characters except hyphens
* Normalize Lithuanian characters to Latin equivalents
* Append .lt TLD to form domains
* Save to `/assets/output/word_transform_*.txt`

Example usage:

```bash
python3 src/main.py word_transform --input assets/input/words.txt --output assets/output/transformed_domains.txt
```

---

### **5. Optional Extras**

* **pattern_generator.py** → Define regex-like patterns (`[a-z]{2}[0-9]{1}` etc.)
* **random_generator.py** → Random combinations with weighted letter frequencies.
* **deduplication tool** → Clean duplicates, invalid TLDs, or domains exceeding 63 chars.

---

### **6. Documentation**

* `/docs/overview.md` → explains the idea
* `/docs/markov.md` → how Markov chains are used and trained
* `/docs/brute.md` → how brute generation works
* `/docs/word_transform.md` → how word transformation works
* `/docs/roadmap.md` → ideas like `AI-based generator`, `semantic-word generator`, etc.

---

## 🧠 **Example Workflow**

```bash
# 1. Train markov model and generate 50k names
python3 src/main.py markov --input assets/input/real_domains.txt --count 50000

# 2. Generate all 2-character .lt combos
python3 src/main.py brute --length 2 --charset a-z0-9

# 3. Combine outputs
cat assets/output/*.txt > assets/output/all_domains.txt

# 4. Use in your external domain scanner repo
```
