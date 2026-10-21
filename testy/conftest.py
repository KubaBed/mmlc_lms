import pathlib
import sys

# logika łącznika nie importuje frappe, więc testy działają bez lokalnej instalacji Frappe
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
