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


def _wrap(text: str, width: int = 88) -> list[str]:
    lines: list[str] = []
    for para in text.splitlines():
        if not para.strip():
            lines.append("")
            continue
        current = ""
        for word in para.split():
            trial = word if not current else f"{current} {word}"
            if len(trial) <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


def write_pdf(src: Path, dest: Path) -> None:
    width, height = 612, 792
    margin, leading, font_size = 54, 14, 11
    lines_per_page = (height - 2 * margin) // leading
    wrapped = _wrap(_latin1(src.read_text(encoding="utf-8")))
    pages = [
        wrapped[i : i + lines_per_page] for i in range(0, len(wrapped), lines_per_page)
    ] or [[]]

    def stream_for(lines: list[str]) -> bytes:
        y = height - margin
        ops = ["BT", f"/F1 {font_size} Tf"]
        for line in lines:
            ops.append(f"1 0 0 1 {margin} {y} Tm ({_escape(line)}) Tj")
            y -= leading
        ops.append("ET")
        return "\n".join(ops).encode("latin-1")

    font_num = 3 + len(pages) * 2
    page_nums = [3 + i * 2 for i in range(len(pages))]
    content_nums = [4 + i * 2 for i in range(len(pages))]
    kids = " ".join(f"{n} 0 R" for n in page_nums)
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode("latin-1"),
    ]
    for i, lines in enumerate(pages):
        stream = stream_for(lines)
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
                f"/Contents {content_nums[i]} 0 R "
                f"/Resources << /Font << /F1 {font_num} 0 R >> >> >>"
            ).encode("latin-1")
        )
        objects.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

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
