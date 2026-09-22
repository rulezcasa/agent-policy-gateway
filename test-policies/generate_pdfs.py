"""Regenerate the demo policy PDFs from the plain-text sources. Stdlib only."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT / "source"


def _latin1(text: str) -> str:
    return (
        text.replace("\u2014", "--")
        .replace("\u2013", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .encode("latin-1", "replace")
        .decode("latin-1")
    )


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_pdf(src: Path, dest: Path) -> None:
    width, height = 612, 792
    margin, leading = 50, 14
    y = height - margin
    ops = ["BT", "/F1 11 Tf"]
    for line in _latin1(src.read_text(encoding="utf-8")).splitlines():
        if y < margin:
            break
        ops.append(f"1 0 0 1 {margin} {y} Tm ({_escape(line)}) Tj")
        y -= leading
    ops.append("ET")
    stream = "\n".join(ops).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
            "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
        ).encode("latin-1"),
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode("latin-1"))
        out.extend(obj)
        out.extend(b"\nendobj\n")

    xref = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    out.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n"
        ).encode("latin-1")
    )
    dest.write_bytes(out)


def main() -> None:
    for src in sorted(SOURCE.glob("*.txt")):
        dest = ROOT / src.with_suffix(".pdf").name
        write_pdf(src, dest)
        print(f"wrote {dest.name}")


if __name__ == "__main__":
    main()
