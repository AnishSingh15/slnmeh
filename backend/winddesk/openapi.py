"""Write the OpenAPI schema, the source of the frontend's generated TypeScript types.

Usage (from backend/):  uv run python -m winddesk.openapi ../frontend/openapi.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from winddesk.main import create_app


def main() -> None:
    out = Path(sys.argv[1])
    out.write_text(json.dumps(create_app().openapi(), indent=2) + "\n")


if __name__ == "__main__":
    main()
