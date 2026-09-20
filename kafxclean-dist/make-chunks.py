import base64
import hashlib
from pathlib import Path

apk = Path("/srv/KafXClean-v1.8.4.apk")
data = apk.read_bytes()
encoded = base64.b64encode(data).decode("ascii")

chunk_dir = Path("/srv/apk-b64-chunks")
chunk_dir.mkdir(exist_ok=True)
chunk_size = 100_000
parts = [encoded[i:i + chunk_size] for i in range(0, len(encoded), chunk_size)]

for index, part in enumerate(parts):
    (chunk_dir / f"part-{index:03d}").write_text(part)

(chunk_dir / "manifest.txt").write_text(
    f"base64_char_count={len(encoded)}\n"
    f"chunk_count={len(parts)}\n"
    f"original_byte_size={len(data)}\n"
    f"sha256={hashlib.sha256(data).hexdigest()}\n"
    f"chunk_size={chunk_size}\n"
)
