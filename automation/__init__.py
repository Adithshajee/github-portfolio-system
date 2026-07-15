"""
automation/ — DEPRECATED COMPATIBILITY LAYER
═════════════════════════════════════════════

⚠️  DEPRECATION NOTICE: GPS v2.0
─────────────────────────────────
This directory (automation/) has been superseded by the new Python package
at src/gps/ and will be REMOVED in GPS v4.0.

Migration Guide:
────────────────
  OLD (v1):  python automation/update_readme.py [--dry-run]
  NEW (v2):  gps run [--dry-run]

  OLD (v1):  python automation/update_readme.py
  NEW (v2):  gps run

  OLD (v1):  python -m unittest tests/test_validation.py
  NEW (v2):  pytest tests/

Install GPS v2:
    pip install -e ".[dev]"

Run GPS v2:
    gps run --dry-run         # Preview output
    gps validate              # Check config + markers
    gps status                # Show provider status

See: https://adithshajee.github.io/github-portfolio-system/setup
"""
