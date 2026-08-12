"""生成最小合法占位 PDF（ASCII 文本，无需中文字体嵌入）。

用法: python make-placeholder-pdf.py <输出路径> ["占位文本"]
例:   python make-placeholder-pdf.py C:/Users/usr/source/repos/x/src/App/wwwroot/resume.pdf "RESUME PLACEHOLDER - to be replaced by owner."

注意（Windows git-bash）: 调用 Windows python 时路径传 C:/... 正斜杠，不要传 /c/...（MSYS 转换会报 No such file）。
"""
import sys


def build(text: bytes) -> bytes:
    stream = b"BT /F1 20 Tf 72 720 Td (" + text + b") Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"

    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    text = sys.argv[2].encode("ascii") if len(sys.argv) > 2 else b"PLACEHOLDER"
    with open(sys.argv[1], "wb") as f:
        f.write(build(text))
    print(f"written {len(build(text))} bytes -> {sys.argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
