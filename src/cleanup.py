from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Set, Tuple
from urllib.parse import urlparse

import tldextract

GOV_DOMAINS: Set[str] = {"lrv", "edu", "mil"}
GOV_SUFFIXES: Set[str] = {"lrv.lt", "edu.lt", "mil.lt", "gov.lt"}


@dataclass
class CleanupResult:
    cleaned_count: int
    skipped_count: int
    processed_count: int
    errors_path: Path


@dataclass
class RemoveResult:
    kept_count: int
    removed_count: int
    output_path: Path


def is_valid_domain_length(domain: str) -> Tuple[bool, Optional[str]]:
    labels = domain.split(".")
    # Validate only domain labels (exclude TLD - the last label)
    domain_labels = labels[:-1] if len(labels) > 1 else labels
    for label in domain_labels:
        if len(label) < 3:
            return False, "domain label too short (min 3 chars)"
        if len(label) > 63:
            return False, "label exceeds 63 characters"
    return True, None


def is_valid_hyphen_rules(domain: str) -> Tuple[bool, Optional[str]]:
    labels = domain.split(".")
    for label in labels:
        if label.startswith("-"):
            return False, "hyphen at start of label"
        if label.endswith("-"):
            return False, "hyphen at end of label"
        # Allow the punycode IDN prefix "xn--" which contains consecutive hyphens
        # while still rejecting other consecutive hyphen sequences.
        if "--" in label and not label.startswith("xn--"):
            return False, "consecutive hyphens"
    return True, None


def process_domain(
    raw: str,
    *,
    target_tld: Optional[str] = "lt",
    allow_other_tlds: bool = False,
    allow_subdomains: bool = False,
    gov_domains: Optional[Set[str]] = None,
    gov_suffixes: Optional[Set[str]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalize and validate a domain string.

    Returns (domain, None) when accepted, or (None, reason) when skipped.
    """
    if raw is None:
        return None, "empty"

    cleaned = raw.strip()
    if not cleaned:
        return None, "empty line"

    cleaned = cleaned.rstrip(".")

    if re.match(r"^[a-zA-Z]+://", cleaned):
        parsed = urlparse(cleaned)
        cleaned = parsed.netloc or cleaned

    if cleaned.lower().startswith("www."):
        cleaned = cleaned[4:]

    if re.match(r"^\d+(\.\d+){3}$", cleaned):
        return None, "ip address"

    if not re.match(r"^[\w\-.]+$", cleaned, re.UNICODE):
        return None, "invalid characters"

    cleaned = cleaned.lower()

    ext = tldextract.extract(cleaned)
    if not ext.domain or not ext.suffix:
        return None, "invalid domain/suffix"

    suffix = ext.suffix
    domain = f"{ext.domain}.{suffix}"

    use_gov_domains = gov_domains or GOV_DOMAINS
    use_gov_suffixes = gov_suffixes or GOV_SUFFIXES

    if target_tld:
        if suffix != target_tld and suffix not in use_gov_suffixes:
            if not allow_other_tlds:
                return None, "disallowed tld"
    if suffix == "lt":
        if suffix in use_gov_suffixes or ext.domain in use_gov_domains:
            if ext.subdomain:
                domain = f"{ext.subdomain}.{domain}"
        elif ext.subdomain and not allow_subdomains:
            return None, "non-govt subdomain"
    else:
        if ext.subdomain and not allow_subdomains:
            return None, "subdomain not allowed"

    is_valid, reason = is_valid_domain_length(domain)
    if not is_valid:
        return None, reason

    is_valid, reason = is_valid_hyphen_rules(domain)
    if not is_valid:
        return None, reason

    return domain, None


def clean_file(
    input_path: Path | str,
    output_path: Optional[Path | str] = None,
    errors_path: Optional[Path | str] = None,
    *,
    target_tld: Optional[str] = "lt",
    allow_other_tlds: bool = False,
    allow_subdomains: bool = False,
    progress_every: int = 1000,
) -> CleanupResult:
    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_file = Path(output_path) if output_path else Path("assets/output") / f"cleanup_{input_file.stem}.txt"
    errors_file = Path(errors_path) if errors_path else output_file.with_suffix(".errors.txt")

    cleaned: Set[str] = set()
    errors: list[tuple[int, str, str]] = []
    processed_count = 0
    skipped_count = 0

    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f, start=1):
            if progress_every and line_num % progress_every == 0:
                print(f"...processed {line_num} lines...")

            stripped = raw_line.rstrip("\n")
            if not stripped.strip():
                continue

            processed_count += 1
            domain, reason = process_domain(
                stripped,
                target_tld=target_tld,
                allow_other_tlds=allow_other_tlds,
                allow_subdomains=allow_subdomains,
            )
            if domain:
                cleaned.add(domain)
            else:
                skipped_count += 1
                errors.append((line_num, stripped, reason or "unknown"))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for domain in sorted(cleaned):
            f.write(domain + "\n")

    errors_file.parent.mkdir(parents=True, exist_ok=True)
    with open(errors_file, "w", encoding="utf-8") as ef:
        for line_num, line_val, reason in errors:
            if reason == "empty line":
                continue
            ef.write(f"Line {line_num}: {reason} | {line_val}\n")

    return CleanupResult(
        cleaned_count=len(cleaned),
        skipped_count=skipped_count,
        processed_count=processed_count,
        errors_path=errors_file,
    )


def remove_domains(
    parent_path: Path | str,
    removees_path: Path | str,
    output_path: Optional[Path | str] = None,
) -> RemoveResult:
    """
    Remove domains in removees_path from parent_path and write the remainder.

    Uses case-insensitive matching on trimmed lines.
    """
    parent_file = Path(parent_path)
    removees_file = Path(removees_path)

    if not parent_file.exists():
        raise FileNotFoundError(f"Parent file not found: {parent_file}")
    if not removees_file.exists():
        raise FileNotFoundError(f"Removees file not found: {removees_file}")

    output_file = Path(output_path) if output_path else parent_file.with_name(
        f"{parent_file.stem}_minus_{removees_file.stem}{parent_file.suffix or '.txt'}"
    )

    with open(removees_file, "r", encoding="utf-8") as f:
        removees = {line.strip().lower() for line in f if line.strip()}

    kept: list[str] = []
    removed_count = 0

    with open(parent_file, "r", encoding="utf-8") as f:
        for line in f:
            domain = line.strip()
            if not domain:
                continue
            if domain.lower() in removees:
                removed_count += 1
            else:
                kept.append(domain)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        for domain in kept:
            f.write(domain + "\n")

    return RemoveResult(
        kept_count=len(kept),
        removed_count=removed_count,
        output_path=output_file,
    )
