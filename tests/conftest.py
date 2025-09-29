import sys
from pathlib import Path

# Ensure repository root is on sys.path so 'gpt_oss_redteam' can be imported in tests
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
