#!/usr/bin/env python3
"""
Dago Domenai Generator - CLI Entry Point

A comprehensive toolkit for generating domain name lists using multiple algorithmic approaches.
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from generators.brute_generator import BruteForceGenerator
from generators.word_transform_generator import WordTransformGenerator
from cleanup import clean_file, remove_domains
from utils.io_utils import make_output_path


def create_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Generate domain name lists using various algorithms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 2-4 character domains with default settings
  python main.py brute

  # Transform words from file to .lt domains
  python main.py word_transform --input assets/input/words.txt

  # Transform words to .com domains with custom output
  python main.py word_transform --input words.txt --tld com --output domains.txt

  # Generate 3-character domains only
  python main.py brute --length 3

  # Generate 3-5 character alphanumeric domains with hyphens
  python main.py brute --min 3 --max 5 --charset alphanumeric --hyphen-mode with

  # Generate only domains that contain hyphens
  python main.py brute --hyphen-mode only --output hyphen_domains.txt

  # Generate numeric domains only
  python main.py brute --charset numbers --min 1 --max 3
        """
    )

    subparsers = parser.add_subparsers(dest='generator', help='Generator type')

    # Cleanup utility
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean and normalize a domain list')
    cleanup_parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input file path (one domain per line)'
    )
    cleanup_parser.add_argument(
        '--output', '-o',
        help='Output file path (default: assets/output/cleanup_<input>.txt)'
    )
    cleanup_parser.add_argument(
        '--errors', '-e',
        help='Error log file path (default: alongside output)'
    )
    cleanup_parser.add_argument(
        '--tld',
        default='lt',
        help='Target TLD to enforce (default: lt)'
    )
    cleanup_parser.add_argument(
        '--allow-subdomains',
        action='store_true',
        help='Allow subdomains for non-governmental domains'
    )
    cleanup_parser.add_argument(
        '--allow-other-tlds',
        action='store_true',
        help='Accept any TLD instead of enforcing --tld only'
    )
    cleanup_parser.add_argument(
        '--removees', '-r',
        help='Optional file of domains to remove from the cleaned output'
    )
    cleanup_parser.add_argument(
        '--remove-output',
        help='Output file path after removal (default: <output> minus <removees>)'
    )

    # Brute force generator
    brute_parser = subparsers.add_parser('brute', help='Brute force domain generation')
    brute_parser.add_argument(
        '--charset', '-c',
        choices=['numbers', 'letters', 'alphanumeric'],
        default='alphanumeric',
        help='Character set to use (default: alphanumeric)'
    )
    brute_parser.add_argument(
        '--min', '-m',
        type=int, default=2,
        help='Minimum domain length (default: 2)'
    )
    brute_parser.add_argument(
        '--max', '-M',
        type=int, default=4,
        help='Maximum domain length (default: 4)'
    )
    brute_parser.add_argument(
        '--length', '-l',
        type=int,
        help='Domain length (sets both min and max to this value)'
    )
    brute_parser.add_argument(
        '--hyphen-mode',
        choices=['with', 'without', 'only'],
        default='with',
        help='Hyphen handling mode (default: with)'
    )
    brute_parser.add_argument(
        '--tld',
        default='lt',
        help='Top-level domain (default: lt)'
    )
    brute_parser.add_argument(
        '--output', '-o',
        help='Output file path (default: auto-generated)'
    )
    brute_parser.add_argument(
        '--estimate-only', '-e',
        action='store_true',
        help='Only estimate count, do not generate'
    )

    # Word transform generator
    word_parser = subparsers.add_parser('word_transform', help='Transform words from file to domains')
    word_parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input file path (one word per line)'
    )
    word_parser.add_argument(
        '--output', '-o',
        help='Output file path (default: auto-generated)'
    )
    word_parser.add_argument(
        '--tld',
        default='lt',
        help='Top-level domain to append (default: lt)'
    )
    word_parser.add_argument(
        '--estimate-only', '-e',
        action='store_true',
        help='Only estimate count, do not generate'
    )

    return parser


def generate_brute_force(args):
    """Handle brute force generation."""
    # Handle --length parameter
    if args.length is not None:
        if args.min != 2 or args.max != 4:  # Check if min/max were also specified
            print("Error: Cannot specify both --length and --min/--max", file=sys.stderr)
            return 1
        args.min = args.max = args.length

    try:
        generator = BruteForceGenerator(
            char_type=args.charset,
            min_len=args.min,
            max_len=args.max,
            hyphen_mode=args.hyphen_mode,
            tld=args.tld
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Estimate count
    estimated = generator.estimate_count()
    print(f"Estimated domains to generate: {estimated:,}")

    if args.estimate_only:
        return 0

    # Generate output filename if not provided
    if not args.output:
        rng = f"{args.min}-{args.max}"
        output_file = make_output_path('brute', charset=args.charset, rng=rng, hyphen=args.hyphen_mode, tld=args.tld)
    else:
        output_file = args.output

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating domains to: {output_file}")

    try:
        count = generator.generate_to_file(str(output_path))
        print(f"Successfully generated {count:,} domains")
        return 0
    except Exception as e:
        print(f"Error during generation: {e}", file=sys.stderr)
        return 1


def generate_word_transform(args):
    """Handle word transform generation."""
    try:
        generator = WordTransformGenerator(
            input_file=args.input,
            tld=args.tld
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Clean and validate with shared rules before persisting
    # (process_domain inside generator enforces the same rules line-by-line)

    # Estimate count
    estimated = generator.estimate_count()
    print(f"Estimated domains to generate: {estimated:,}")

    if args.estimate_only:
        return 0

    # Generate output filename if not provided
    if not args.output:
        input_name = Path(args.input).stem
        output_file = make_output_path('word_transform', input=input_name, tld=args.tld)
    else:
        output_file = args.output

    # Ensure output directory exists
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating domains to: {output_file}")

    try:
        count = generator.generate_to_file(str(output_path))
        print(f"Successfully generated {count:,} domains")
        return 0
    except Exception as e:
        print(f"Error during generation: {e}", file=sys.stderr)
        return 1


def run_cleanup(args):
    """Handle standalone cleanup of domain lists."""
    input_path = Path(args.input)
    output_path = Path(args.output) if args.output else Path(f"assets/output/cleanup_{input_path.stem}.txt")
    errors_path = Path(args.errors) if args.errors else output_path.with_suffix('.errors.txt')

    try:
        result = clean_file(
            input_path,
            output_path,
            errors_path,
            target_tld=args.tld,
            allow_other_tlds=args.allow_other_tlds,
            allow_subdomains=args.allow_subdomains,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"Cleaned {result.cleaned_count} unique domains to {output_path}")
    print(f"Processed {result.processed_count} non-empty lines")
    if result.skipped_count:
        print(f"Skipped {result.skipped_count} lines; see {result.errors_path} for details")
    if args.removees:
        try:
            remove_result = remove_domains(
                output_path,
                Path(args.removees),
                Path(args.remove_output) if args.remove_output else None,
            )
        except FileNotFoundError as e:
            print(f"Error during removal: {e}", file=sys.stderr)
            return 1
        print(f"Removed {remove_result.removed_count} domains using {args.removees}")
        print(f"Kept {remove_result.kept_count} domains -> {remove_result.output_path}")
    return 0


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.generator:
        parser.print_help()
        return 1

    if args.generator == 'brute':
        return generate_brute_force(args)
    elif args.generator == 'word_transform':
        return generate_word_transform(args)
    elif args.generator == 'cleanup':
        return run_cleanup(args)
    else:
        print(f"Generator '{args.generator}' not implemented yet", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())