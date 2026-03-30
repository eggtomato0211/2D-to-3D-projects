from dataclasses import dataclass
from typing import Optional

@datackas
class BluePrint:
    id: str
    file_path: str
    file_name: str
    width: Optional[int] = None
    height: Optional[int] = None
