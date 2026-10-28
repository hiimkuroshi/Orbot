"""Write the Windows version resource (file properties) that PyInstaller embeds in Orbot."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from orbot import __version__  # noqa: E402

numbers = tuple(int(part) for part in __version__.split("."))
version = (numbers + (0, 0, 0, 0))[:4]
template = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version},
    prodvers={version},
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0),
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'Tyr (hiimkuroshi)'),
        StringStruct('FileDescription', 'Orbot Discord Quests desktop app'),
        StringStruct('FileVersion', '{__version__}'),
        StringStruct('InternalName', 'Orbot'),
        StringStruct('LegalCopyright', 'Copyright (c) 2026 Tyr. MIT License.'),
        StringStruct('OriginalFilename', 'Orbot.exe'),
        StringStruct('ProductName', 'Orbot'),
        StringStruct('ProductVersion', '{__version__}'),
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])]),
  ],
)
"""
output = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "build" / "version_info.txt"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(template, encoding="utf-8")
print(output)
