"""修正 WPS 保存 docx 后 word/styles.xml 的元素顺序。

背景：`tools/build_manual.js` 用 docx-js 生成的文档是符合 OOXML Schema 的；
但用 WPS 打开 → 更新目录域 → 保存后，WPS 会把部分 `<w:style>` 的子元素重排
（例如把 `w:uiPriority` 放到 `w:qSemihidden` / `w:qFormat` 之后），
严格校验器会报 “uiPriority: This element is not expected”。

这个脚本只改 `word/styles.xml`，按 OOXML 规定顺序重排每个 `<w:style>` 的子元素，
其余 zip 条目原样保留，因此不会影响正文、目录域或图片。

用法：.venv\\Scripts\\python.exe tools\\fix_docx_styles.py docs\\使用说明书.docx
"""

import os
import shutil
import sys
import zipfile

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}

# CT_Style 子元素的规定顺序（OOXML 第 17.7.4.17 节）
ORDER = [
    "name", "aliases", "basedOn", "next", "link", "autoRedefine", "hidden",
    "uiPriority", "semiHidden", "unhideWhenUsed", "qFormat", "locked",
    "personal", "personalCompose", "personalReply", "rsid",
    "pPr", "rPr", "tblPr", "trPr", "tcPr", "tblStylePr",
]
INDEX = {name: i for i, name in enumerate(ORDER)}


def fix_styles(xml_bytes: bytes) -> tuple:
    root = etree.fromstring(xml_bytes)
    changed = 0
    for style in root.findall("w:style", NS):
        children = list(style)
        ordered = sorted(children, key=lambda el: INDEX.get(etree.QName(el).localname, len(ORDER)))
        before = [etree.QName(c).localname for c in children]
        after = [etree.QName(c).localname for c in ordered]
        if before != after:
            for child in children:
                style.remove(child)
            for child in ordered:
                style.append(child)
            changed += 1
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True), changed


def main(path: str) -> int:
    if not os.path.exists(path):
        print(f"文件不存在：{path}")
        return 1

    backup = path + ".bak"
    shutil.copyfile(path, backup)

    with zipfile.ZipFile(path) as zin:
        entries = [(info, zin.read(info.filename)) for info in zin.infolist()]

    fixed_total = 0
    output = []
    for info, data in entries:
        if info.filename == "word/styles.xml":
            data, fixed_total = fix_styles(data)
        output.append((info, data))

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
        for info, data in output:
            item = zipfile.ZipInfo(info.filename, date_time=info.date_time)
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = info.external_attr
            zout.writestr(item, data)

    os.remove(backup)
    print(f"已重排 {fixed_total} 个样式的子元素顺序：{path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法：python tools/fix_docx_styles.py <docx 路径>")
        raise SystemExit(1)
    raise SystemExit(main(sys.argv[1]))
