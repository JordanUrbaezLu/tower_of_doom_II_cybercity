"""Switch the saved preview to the native-card state without resaving."""
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from native_card_preview import select
select('after_reveal')
