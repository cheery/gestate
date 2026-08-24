"""`tools/prereg.sh` — a trial sheet that cannot decide is refused.

Kaizen of 2026-08-24: three sheets on 2026-08-23 each named a fault that
voided the run, in prose, and the arms started anyway.  The check reads
three lines and nothing else, and these tests pin that it refuses on a
blank one, on a non-numeric `n:`, and passes a sheet with all three.
"""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "prereg.sh"


def run(tmp_path, text):
    f = tmp_path / "preregistration.md"
    f.write_text(text, encoding="utf-8")
    return subprocess.run(["bash", str(TOOL), str(f)], capture_output=True, text=True)


def test_a_sheet_with_all_three_passes(tmp_path):
    r = run(tmp_path, "# sheet\n\ndecision: keep or drop the pointer\ncontrol: clone with no memory dir\nn: 5\n")
    assert r.returncode == 0, r.stdout + r.stderr


def test_a_blank_control_is_refused_and_named(tmp_path):
    r = run(tmp_path, "decision: something\ncontrol:\nn: 5\n")
    assert r.returncode == 1
    assert "BLANK   control:" in r.stdout


def test_a_missing_line_counts_as_blank(tmp_path):
    r = run(tmp_path, "decision: something\nn: 5\n")
    assert r.returncode == 1
    assert "control:" in r.stdout


def test_n_must_be_a_number(tmp_path):
    r = run(tmp_path, "decision: d\ncontrol: c\nn: a few\n")
    assert r.returncode == 1
    assert "not a number" in r.stdout


def test_bold_markdown_keys_are_read(tmp_path):
    r = run(tmp_path, "**decision:** d\n**control:** c\n**n:** 3\n")
    assert r.returncode == 0, r.stdout


def test_no_file_is_a_usage_error(tmp_path):
    r = subprocess.run(["bash", str(TOOL)], capture_output=True, text=True)
    assert r.returncode == 2
