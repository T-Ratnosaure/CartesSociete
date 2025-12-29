# Regulatory Audit Report

**Auditor**: Wealon, Regulatory Team
**Date**: 2025-12-29
**Scope**: Card System Implementation (models.py, repository.py, renderer.py, validate_cards.py, JSON data files)
**Verdict**: MAJOR ISSUES IDENTIFIED

---

## Executive Summary

*Sighs heavily*

I see we've decided to build a card game system. How... creative. While there is evidence of *some* adherence to the CLAUDE.md coding standards (I'll admit the type hints are present - finally, someone read the requirements), I have identified **15 issues** across security, code quality, and architecture categories.

The most concerning finding is the **complete lack of HTML escaping in the renderer module**, which opens the door to Cross-Site Scripting (XSS) attacks. I've noted this type of vulnerability before in other projects, and yet here we are again. Additionally, there's a path traversal vulnerability in the card image handling that could allow malicious JSON data to reference files outside the intended directory.

Per regulatory requirements, this code CANNOT be deployed to production until the Critical issues are resolved.

---

## Critical Issues (Security Vulnerabilities)

### CRIT-001: Cross-Site Scripting (XSS) in HTML Renderer

**File**: `C:\Users\larai\CartesSociete\src\cards\renderer.py`
**Lines**: 95-196 (entire `render_card_html` function)
**Severity**: CRITICAL

The `render_card_html` function directly interpolates user-controllable card data into HTML without any escaping or sanitization. Card names, ability effects, bonus text, and other fields from JSON files are inserted directly into the HTML output using f-strings.

**Vulnerable code pattern (line 164)**:
```python
image_html = (
    f'<div class="card-image"><img src="{image_src}" alt="{card.name}" /></div>'
)
```

**And throughout lines 167-195**:
```python
html = f"""
<div class="card {type_class} {level_class}" data-card-id="{card.id}">
    ...
    <span class="name">{card.name}</span>
    ...
    {bonus_html}
    ...
</div>
"""
```

**Attack Vector**: If a malicious actor can inject card data (e.g., `card.name = '<script>alert("XSS")</script>'`), this JavaScript will execute in any browser rendering the HTML output.

**Required Fix**: Use `html.escape()` from the `html` module for ALL user-controllable strings before HTML interpolation.

---

### CRIT-002: Path Traversal Vulnerability in Image Path Handling

**File**: `C:\Users\larai\CartesSociete\src\cards\renderer.py`
**Lines**: 114-118
**Severity**: CRITICAL

The `image_path` field from card JSON data is used directly without validation:

```python
if image_base_path:
    image_src = str(image_base_path / card.image_path)
else:
    image_src = card.image_path
```

**Attack Vector**: A malicious `image_path` like `"../../../etc/passwd"` or `"..\\..\\..\\Windows\\System32\\config\\SAM"` could reference sensitive files. While this may not directly expose file contents in all contexts, it violates the principle of path confinement.

**Required Fix**: Validate that the resolved path stays within the intended image directory using `Path.resolve()` and checking it's a child of the base path.

---

### CRIT-003: Path Traversal in Card Repository JSON Loading

**File**: `C:\Users\larai\CartesSociete\src\cards\repository.py`
**Lines**: 137
**Severity**: HIGH

The repository uses `glob("**/*.json")` which is safe, but there's no validation that loaded JSON files actually reside within the expected directory:

```python
for json_file in self.data_dir.glob("**/*.json"):
```

If symlinks exist or `data_dir` is user-controllable, arbitrary JSON files could be loaded.

**Required Fix**: Resolve paths and verify they remain within the data directory.

---

## Major Issues (Code Quality & Security)

### MAJ-001: No Input Validation on JSON Card Data

**File**: `C:\Users\larai\CartesSociete\src\cards\repository.py`
**Lines**: 58-104 (`_parse_card` function)
**Severity**: MAJOR

While the card models have validation in `__post_init__`, the JSON parsing blindly accesses dictionary keys without validation. A malformed JSON file could cause KeyError exceptions or inject unexpected data types.

**Example (line 70-72)**:
```python
card_type = CardType(data["card_type"])
family = Family(data["family"])
card_class = CardClass(data["card_class"])
```

**Required Fix**:
1. Validate JSON against the schema (`schema.json`) before parsing
2. Use `.get()` with explicit type checking and defaults
3. Wrap in try/except with meaningful error messages

---

### MAJ-002: Global Mutable State in Repository Singleton

**File**: `C:\Users\larai\CartesSociete\src\cards\repository.py`
**Lines**: 333-346
**Severity**: MAJOR

The `_default_repository` global variable creates mutable global state that can lead to test pollution and thread-safety issues:

```python
_default_repository: CardRepository | None = None

def get_repository() -> CardRepository:
    global _default_repository
    if _default_repository is None:
        _default_repository = CardRepository()
    return _default_repository
```

**Required Fix**: Consider using a proper dependency injection pattern or at minimum provide a `reset_repository()` function for testing.

---

### MAJ-003: Hardcoded Path in validate_cards.py

**File**: `C:\Users\larai\CartesSociete\scripts\validate_cards.py`
**Line**: 301
**Severity**: MAJOR

Per CLAUDE.md: "NEVER hardcode game values (use configs)"

```python
default=Path("C:/Users/larai/cartes_societe"),
```

This hardcoded Windows path will break on any other system or user account.

**Required Fix**: Use environment variables or a config file for default paths.

---

### MAJ-004: sys.path Manipulation

**File**: `C:\Users\larai\CartesSociete\scripts\validate_cards.py`
**Lines**: 14-15
**Severity**: MAJOR

```python
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

This is a fragile import pattern that can lead to import confusion. As I've noted seventeen times before in other audits, this approach is problematic.

**Required Fix**: Use proper package installation (`pip install -e .`) or run scripts as modules (`python -m scripts.validate_cards`).

---

### MAJ-005: Missing Error Context in Repository Loading

**File**: `C:\Users\larai\CartesSociete\src\cards\repository.py`
**Lines**: 141-153
**Severity**: MAJOR

When JSON parsing fails, there's no indication of which file caused the error:

```python
with open(json_file, encoding="utf-8") as f:
    data = json.load(f)
```

**Required Fix**: Wrap in try/except and include the filename in error messages.

---

## Minor Issues (Style & Best Practices)

### MIN-001: Dead Import in validate_cards.py

**File**: `C:\Users\larai\CartesSociete\scripts\validate_cards.py`
**Line**: 17
**Severity**: MINOR

`CardRenderer` is imported but only used in one branch. The import at the top level means it's always loaded:

```python
from cards import CardRenderer, CardRepository
```

**Required Fix**: Move `CardRenderer` import inside the `generate_gallery` branch for lazy loading.

---

### MIN-002: Inconsistent Return Type Annotations

**File**: `C:\Users\larai\CartesSociete\src\cards\repository.py`
**Line**: 158
**Severity**: MINOR

The `get` method returns `Card | None`, but callers might expect specific card types:

```python
def get(self, card_id: str) -> Card | None:
```

Consider adding overloaded signatures or generic type parameters for type-safe retrieval.

---

### MIN-003: Unused Variable in create_card_id

**File**: `C:\Users\larai\CartesSociete\src\cards\models.py`
**Lines**: 206-227
**Severity**: MINOR

The function performs many string replacements that could be simplified:

```python
normalized = normalized.replace("e", "e")  # (accent normalization)
normalized = normalized.replace("e", "e")
# ... many more
```

**Required Fix**: Use `unicodedata.normalize('NFD', name)` and filter combining characters for cleaner accent stripping.

---

### MIN-004: Placeholder Test File Still Present

**File**: `C:\Users\larai\CartesSociete\tests\test_placeholder.py`
**Severity**: MINOR

The file itself says "These tests should be replaced." I agree. Why is this still here?

---

### MIN-005: Missing Docstring for render_card_gallery_html

**File**: `C:\Users\larai\CartesSociete\src\cards\renderer.py`
**Line**: 382-436
**Severity**: MINOR

Per CLAUDE.md: "Docstrings (REQUIRED for public APIs)"

The function has a docstring, but it doesn't document all return characteristics (e.g., that it returns a complete HTML document with DOCTYPE).

---

### MIN-006: Line Length Violation Potential

**File**: `C:\Users\larai\CartesSociete\src\cards\renderer.py`
**Various lines
**Severity**: MINOR

Per CLAUDE.md, line length maximum is 88 characters. The CSS string at lines 205-379 contains very long lines that should be broken up.

---

## Dead Code Found

| Location | Item | Notes |
|----------|------|-------|
| `scripts/validate_cards.py:29-37` | `find_image_files` function | Function is defined but never called anywhere in the codebase |
| `tests/test_placeholder.py` | Entire file | Contains only placeholder tests that add no value |

---

## Testing Gaps Identified

### TEST-001: No XSS Attack Vector Tests

The renderer tests don't include any tests with malicious input strings containing HTML/JavaScript. This is a significant gap given the XSS vulnerability.

### TEST-002: No Path Traversal Tests

No tests verify that malicious image paths are rejected.

### TEST-003: No JSON Schema Validation Tests

The schema.json file exists but is never used in tests to validate card data.

### TEST-004: No Error Handling Tests for Malformed JSON

Tests don't cover scenarios where JSON files are malformed or contain unexpected data types.

---

## Recommendations (Ordered by Priority)

1. **IMMEDIATE**: Add HTML escaping to ALL user-controllable strings in `render_card_html()` using `html.escape()`

2. **IMMEDIATE**: Add path validation to ensure `image_path` cannot escape the intended directory

3. **HIGH**: Implement JSON schema validation using `jsonschema` library against `schema.json`

4. **HIGH**: Remove hardcoded path from `validate_cards.py` and use environment variable or config

5. **MEDIUM**: Add proper error handling with file context to repository JSON loading

6. **MEDIUM**: Replace `sys.path` manipulation with proper package structure

7. **MEDIUM**: Add security-focused test cases for XSS and path traversal

8. **LOW**: Remove dead code (`find_image_files` function, placeholder tests)

9. **LOW**: Consider using `unicodedata` for accent normalization in `create_card_id`

10. **LOW**: Add reset mechanism for repository singleton for test isolation

---

## Positive Observations

*grudgingly*

Fine. I'll admit there are some things done correctly:

- Type hints are present throughout (per CLAUDE.md requirements)
- Docstrings exist on most public functions
- Test coverage exists for the happy paths
- The data model design with frozen dataclasses is appropriate
- Proper use of `__all__` in `__init__.py`
- Enum usage for type safety on card types, families, and classes

---

## Auditor's Notes

I've been doing this for years, and yet developers continue to forget basic security practices like HTML escaping. The XSS vulnerability in `renderer.py` is particularly egregious because this is clearly a web-facing feature designed to render cards in browsers.

The path traversal issues suggest a fundamental misunderstanding of file path security. Every path from external sources (JSON files loaded from disk) should be treated as hostile input.

The tests are... adequate for basic functionality, but completely ignore security considerations. This is a pattern I see repeatedly. "It works!" is not the same as "It's secure."

At least the type hints are there. Small victories.

---

**Compliance Status**: NON-COMPLIANT
**Re-audit Required**: YES (after Critical issues resolved)
**Next Review**: Upon receipt of fix confirmation

---

*I'll be watching.*

---

**Wealon**
Regulatory Team
*"Security is not optional."*
