"""Switch the saved preview to its honest before-jump state without resaving."""
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from native_card_preview import select
select('before_jump')
