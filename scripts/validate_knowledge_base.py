#!/usr/bin/env python3
"""
Knowledge Base Validation Script

Purpose: Validate .kd files for KDL syntax compliance, .kd/.md pairing,
         and orphaned references

Usage:
    python3 scripts/validate_knowledge_base.py

Returns:
    Exit code 0 if all validations pass, 1 if any fail
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Set


# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.CYAN}{text}{Colors.RESET}")


def get_project_root() -> Path:
    """Get project root directory."""
    # Script is in scripts/, project root is parent
    return Path(__file__).parent.parent


def validate_kdl_syntax(line: str, line_number: int, filename: str) -> Tuple[bool, str]:
    """
    Validate KDL syntax for a single line.

    Pattern: <category>::<type>::<name>:<primary-id>|<key>:<value>|...

    Args:
        line: Line to validate
        line_number: Line number in file
        filename: File name for error reporting

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    # Strip whitespace
    line = line.strip()

    # Skip empty lines and comments
    if not line or line.startswith('#'):
        return True, ""

    # KDL pattern: category::type::name:id|key:value|...
    # Pattern allows:
    # - category: lowercase letters
    # - type: lowercase letters, numbers, hyphens
    # - name: lowercase letters, numbers, hyphens
    # - id: anything except pipe
    # - attributes: key (letters, numbers, hyphens, underscores) : value (anything except pipe)
    pattern = r'^[a-z]+::[a-z0-9-]+::[a-z0-9-]+:[^|]+(\|[a-z0-9_-]+:[^|]+)*$'

    if not re.match(pattern, line):
        return False, f"{filename}:{line_number} - Invalid KDL syntax: {line}"

    # Additional validations

    # Check for double colons in wrong places
    if ':::' in line:
        return False, f"{filename}:{line_number} - Triple colon found (should be double): {line}"

    # Check for empty values
    if '||' in line or line.endswith('|'):
        return False, f"{filename}:{line_number} - Empty attribute value: {line}"

    # Check for missing separators
    parts = line.split('::')
    if len(parts) < 3:
        return False, f"{filename}:{line_number} - Missing category/type/name separator: {line}"

    # Check category is lowercase
    category = parts[0]
    if not category.islower():
        return False, f"{filename}:{line_number} - Category must be lowercase: {category}"

    # Check for spaces in structural components (before first |)
    main_part = line.split('|')[0]
    if ' ' in main_part.replace(' ', ''):  # Remove spaces to check
        # Actually, values can have spaces, so check only structure
        structure = main_part.split(':')
        for part in structure[:4]:  # category, type, name, id
            if ' ' in part:
                return False, f"{filename}:{line_number} - Space in structural component: {part}"

    return True, ""


def validate_kd_file(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Validate a single .kd file.

    Args:
        filepath: Path to .kd file

    Returns:
        Tuple of (all_valid: bool, errors: List[str])
    """
    errors = []
    all_valid = True

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_number, line in enumerate(lines, start=1):
            is_valid, error_msg = validate_kdl_syntax(line, line_number, filepath.name)
            if not is_valid:
                errors.append(error_msg)
                all_valid = False

    except FileNotFoundError:
        errors.append(f"File not found: {filepath}")
        all_valid = False
    except Exception as e:
        errors.append(f"Error reading {filepath}: {e}")
        all_valid = False

    return all_valid, errors


def check_kd_md_pairing(project_root: Path) -> Tuple[bool, List[str]]:
    """
    Check that all .kd files have corresponding .md files.

    Expected pairings:
    - .claude/knowledge/*.kd → docs/*.md
    - Exception: _schema.md (KDL spec, no .kd equivalent)

    Args:
        project_root: Project root directory

    Returns:
        Tuple of (all_paired: bool, errors: List[str])
    """
    errors = []
    all_paired = True

    knowledge_dir = project_root / '.claude' / 'knowledge'
    docs_dir = project_root / 'docs'

    if not knowledge_dir.exists():
        errors.append(f"Knowledge directory not found: {knowledge_dir}")
        return False, errors

    if not docs_dir.exists():
        errors.append(f"Docs directory not found: {docs_dir}")
        return False, errors

    # Get all .kd files
    kd_files = list(knowledge_dir.glob('*.kd'))

    # Expected pairings
    pairings = {
        'code-architecture.kd': 'architecture.md',
        'deployment-flows.kd': 'deployment-procedures.md',
        'troubleshooting.kd': 'troubleshooting.md',  # Should exist or be created
        'environment-config.kd': 'environment-config.md',  # Should exist or be created
        'agent-workflows.kd': 'agent-workflows.md'
    }

    for kd_file in kd_files:
        kd_name = kd_file.name

        # Skip _schema.md check (special case)
        if kd_name.startswith('_'):
            continue

        if kd_name not in pairings:
            errors.append(f"No expected pairing defined for: {kd_name}")
            all_paired = False
            continue

        expected_md = pairings[kd_name]
        md_path = docs_dir / expected_md

        if not md_path.exists():
            errors.append(f"Missing .md file for {kd_name}: Expected {md_path}")
            all_paired = False

    return all_paired, errors


def find_file_references(filepath: Path) -> Set[str]:
    """
    Find file references in a .kd file.

    Looks for patterns like:
    - file:<path>
    - <path> in primary-id position

    Args:
        filepath: Path to .kd file

    Returns:
        Set of file references found
    """
    references = set()

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Extract primary-id and attributes
            if '|' in line:
                main_part = line.split('|')[0]
                attributes = line.split('|')[1:]
            else:
                main_part = line
                attributes = []

            # Extract primary-id (fourth colon-separated component)
            parts = main_part.split(':')
            if len(parts) >= 4:
                primary_id = parts[3]
                # Check if it looks like a file path
                if '/' in primary_id or primary_id.endswith('.py') or primary_id.endswith('.yaml'):
                    references.add(primary_id)

            # Extract file: attributes
            for attr in attributes:
                if attr.startswith('file:'):
                    file_ref = attr.split(':', 1)[1]
                    references.add(file_ref)

    except Exception as e:
        print_warning(f"Error reading {filepath}: {e}")

    return references


def check_orphaned_references(project_root: Path) -> Tuple[bool, List[str]]:
    """
    Check for orphaned file references in .kd files.

    Validates that files referenced in .kd files actually exist.

    Args:
        project_root: Project root directory

    Returns:
        Tuple of (all_valid: bool, errors: List[str])
    """
    errors = []
    all_valid = True

    knowledge_dir = project_root / '.claude' / 'knowledge'

    if not knowledge_dir.exists():
        errors.append(f"Knowledge directory not found: {knowledge_dir}")
        return False, errors

    kd_files = list(knowledge_dir.glob('*.kd'))

    for kd_file in kd_files:
        references = find_file_references(kd_file)

        for ref in references:
            # Try to resolve file path
            # Could be absolute or relative to project root
            if ref.startswith('/'):
                # Absolute path (likely on Pi, can't validate)
                continue

            # Relative to project root
            file_path = project_root / ref

            if not file_path.exists():
                # Check if it's a Pi-side path (contains /etc/pihole, /opt/pihole-manager)
                if '/etc/pihole' in ref or '/opt/pihole-manager' in ref or '/var/log' in ref:
                    # Pi-side path, can't validate locally
                    continue

                errors.append(f"Orphaned reference in {kd_file.name}: {ref} (not found at {file_path})")
                all_valid = False

    return all_valid, errors


def check_duplicate_entries(project_root: Path) -> Tuple[bool, List[str]]:
    """
    Check for duplicate KDL entries across .kd files.

    Duplicate detection based on category::type::name:primary-id (full unique identifier).

    Args:
        project_root: Project root directory

    Returns:
        Tuple of (no_duplicates: bool, errors: List[str])
    """
    errors = []
    no_duplicates = True

    knowledge_dir = project_root / '.claude' / 'knowledge'

    if not knowledge_dir.exists():
        errors.append(f"Knowledge directory not found: {knowledge_dir}")
        return False, errors

    kd_files = list(knowledge_dir.glob('*.kd'))

    # Track entries: category::type::name:primary-id → (filename, line_number)
    entries: Dict[str, List[Tuple[str, int]]] = {}

    for kd_file in kd_files:
        try:
            with open(kd_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_number, line in enumerate(lines, start=1):
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Extract category::type::name:primary-id (full unique identifier)
                if '|' in line:
                    main_part = line.split('|')[0]
                else:
                    main_part = line

                # Use full identifier as key
                key = main_part

                if key not in entries:
                    entries[key] = []

                entries[key].append((kd_file.name, line_number))

        except Exception as e:
            print_warning(f"Error reading {kd_file}: {e}")

    # Check for duplicates
    for key, locations in entries.items():
        if len(locations) > 1:
            location_str = ", ".join([f"{name}:{line}" for name, line in locations])
            errors.append(f"Duplicate entry '{key}' found at: {location_str}")
            no_duplicates = False

    return no_duplicates, errors


def validate_category_consistency(project_root: Path) -> Tuple[bool, List[str]]:
    """
    Validate that categories used in .kd files are defined in _schema.md.

    Args:
        project_root: Project root directory

    Returns:
        Tuple of (all_valid: bool, warnings: List[str])
    """
    warnings = []
    all_valid = True

    knowledge_dir = project_root / '.claude' / 'knowledge'
    schema_file = knowledge_dir / '_schema.md'

    if not schema_file.exists():
        warnings.append(f"Schema file not found: {schema_file}")
        return False, warnings

    # Extract defined categories from schema
    defined_categories = set()

    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for category sections (### `<category>` pattern)
        category_pattern = r'###\s+`([a-z]+)`\s+-'
        matches = re.findall(category_pattern, content)
        defined_categories.update(matches)

    except Exception as e:
        warnings.append(f"Error reading schema file: {e}")
        return False, warnings

    # Extract categories used in .kd files
    used_categories = set()
    kd_files = list(knowledge_dir.glob('*.kd'))

    for kd_file in kd_files:
        try:
            with open(kd_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue

                # Extract category (first :: separated part)
                parts = line.split('::')
                if len(parts) >= 1:
                    category = parts[0]
                    used_categories.add(category)

        except Exception as e:
            print_warning(f"Error reading {kd_file}: {e}")

    # Check for undefined categories
    undefined = used_categories - defined_categories

    if undefined:
        for category in sorted(undefined):
            warnings.append(f"Category '{category}' used in .kd files but not defined in _schema.md")
        all_valid = False

    return all_valid, warnings


def main():
    """Main validation entry point."""
    project_root = get_project_root()

    print_header("Knowledge Base Validation")
    print_info(f"Project root: {project_root}\n")

    all_checks_passed = True

    # ========================================
    # Check 1: KDL Syntax Validation
    # ========================================
    print_header("1. KDL Syntax Validation")

    knowledge_dir = project_root / '.claude' / 'knowledge'

    if not knowledge_dir.exists():
        print_error(f"Knowledge directory not found: {knowledge_dir}")
        return 1

    kd_files = list(knowledge_dir.glob('*.kd'))

    if not kd_files:
        print_warning("No .kd files found")
    else:
        print_info(f"Found {len(kd_files)} .kd file(s) to validate\n")

        for kd_file in kd_files:
            is_valid, errors = validate_kd_file(kd_file)

            if is_valid:
                print_success(f"{kd_file.name} - Valid KDL syntax")
            else:
                print_error(f"{kd_file.name} - FAILED")
                for error in errors:
                    print(f"  {error}")
                all_checks_passed = False

    # ========================================
    # Check 2: .kd / .md Pairing
    # ========================================
    print_header("2. .kd / .md File Pairing")

    all_paired, errors = check_kd_md_pairing(project_root)

    if all_paired:
        print_success("All .kd files have corresponding .md files")
    else:
        print_error("Missing .md file pairings:")
        for error in errors:
            print(f"  {error}")
        all_checks_passed = False

    # ========================================
    # Check 3: Orphaned References
    # ========================================
    print_header("3. Orphaned File References")

    no_orphans, errors = check_orphaned_references(project_root)

    if no_orphans:
        print_success("No orphaned file references found")
    else:
        print_error("Orphaned file references detected:")
        for error in errors:
            print(f"  {error}")
        all_checks_passed = False

    # ========================================
    # Check 4: Duplicate Entries
    # ========================================
    print_header("4. Duplicate Entry Detection")

    no_duplicates, errors = check_duplicate_entries(project_root)

    if no_duplicates:
        print_success("No duplicate entries found")
    else:
        print_error("Duplicate entries detected:")
        for error in errors:
            print(f"  {error}")
        all_checks_passed = False

    # ========================================
    # Check 5: Category Consistency
    # ========================================
    print_header("5. Category Consistency")

    categories_valid, warnings = validate_category_consistency(project_root)

    if categories_valid:
        print_success("All categories are defined in _schema.md")
    else:
        print_warning("Undefined categories found:")
        for warning in warnings:
            print(f"  {warning}")
        # Note: This is a warning, not a failure
        print_info("\n(This is a warning - validation can still pass)")

    # ========================================
    # Summary
    # ========================================
    print_header("Validation Summary")

    if all_checks_passed:
        print_success("✓ All validation checks PASSED")
        print("\nKnowledge base is valid and ready for agent consumption.\n")
        return 0
    else:
        print_error("✗ Some validation checks FAILED")
        print("\nPlease fix the errors above before proceeding.\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
