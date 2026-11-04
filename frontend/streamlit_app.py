from pathlib import Path

page = Path(__file__).resolve().parent / "pages" / "1_Job_Discovery.py"
exec(compile(page.read_text(encoding="utf-8-sig"), str(page), "exec"))
