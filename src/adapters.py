import json
import re
from typing import Any


def parse_archive(content: str) -> list[dict[str, Any]]:
    cleaned = re.sub(r"window\.YTD\.\w+\.part0\s*=\s*", "", content)
    return json.loads(cleaned)
