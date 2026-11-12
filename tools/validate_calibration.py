"""Check calibration profile structure without claiming physical verification."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.geometry import validate_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', type=Path)
    args = parser.parse_args()
    try:
        profile = json.loads(args.profile.read_text(encoding='utf-8'))
        errors = validate_profile(profile)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    print(json.dumps({'structurally_valid': not errors, 'errors': errors,
                      'physical_calibration_verified': False}, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
