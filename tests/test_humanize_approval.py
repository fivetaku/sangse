"""Offline approval regressions through the real humanize CLI."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import final
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/sangse/scripts/humanize_cuts.py"
SOURCE = "## C01 · K2 · Q2 · h=1050\nheadline: 제품 안내\nbody: |\n  가방에 담아요\nbg: #FFFFFF\n"


@final
class HumanizeApprovalTests(unittest.TestCase):
    def __init__(self, methodName: str = "runTest"):
        super().__init__(methodName)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.source = self.base / "cuts.md"
        self.preview = self.base / "cuts.humanized.md"
        self.report_path = self.base / "qa/humanize.json"
        self.backup = self.base / "cuts.original.md"
        self.response = self.base / "response.json"
        self.source.write_text(SOURCE, encoding="utf-8")
        # An empty PATH makes Codex unavailable even on a developer's machine.
        self.bin = self.base / "empty-bin"
        self.bin.mkdir()
        self.env = {**os.environ, "PATH": str(self.bin)}

    def invoke(self, *args: str):
        return subprocess.run([sys.executable, str(SCRIPT), str(self.base), *args],
                              env=self.env, capture_output=True, text=True, timeout=15)

    def generate(self, body: str = "가방에 쏙 담아요"):
        self.response.write_text(json.dumps({"cuts": [{"id": "C01", "body": [body]}]}),
                                 encoding="utf-8")
        run = self.invoke("--category", "health_food", "--from-json", str(self.response))
        self.assertEqual(run.returncode, 0, run.stderr)
        return json.loads(self.report_path.read_text(encoding="utf-8"))

    def assert_failure(self, code: str, *args: str):
        before = {p: p.read_bytes() for p in (self.source, self.preview, self.report_path, self.backup)
                  if p.exists()}
        run = self.invoke("--apply", *args)
        self.assertNotEqual(run.returncode, 0, run.stdout)
        self.assertIn(code, run.stderr)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        if self.backup not in before:
            self.assertFalse(self.backup.exists())

    def test_regex_bans_reject_and_keep_original_cut(self):
        for body in ("세계 최초", "세계최초", "世界 최초", "피로가 사라져요"):
            with self.subTest(body=body):
                report = self.generate(body)
                self.assertEqual(report["accepted"], [])
                self.assertEqual([cut["id"] for cut in report["rejected"]], ["C01"])
                self.assertIn("가방에 담아요", self.preview.read_text(encoding="utf-8"))
                self.assertNotIn(body, self.preview.read_text(encoding="utf-8"))

    def test_regex_existing_ban_and_negative_lookahead(self):
        self.source.write_text(SOURCE.replace("가방에 담아요", "세계 최초 제품"), encoding="utf-8")
        for body in ("세계 최초 안내", "예방접종 안내"):
            with self.subTest(body=body):
                self.assertEqual([c["id"] for c in self.generate(body)["accepted"]], ["C01"])

    def test_preview_hashes_bind_exact_bytes_without_applying(self):
        original = self.source.read_bytes().replace(b"\n", b"\r\n")
        self.source.write_bytes(original)
        report = self.generate()
        self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(report["output_sha256"], hashlib.sha256(self.preview.read_bytes()).hexdigest())
        self.assertFalse(report["applied"])
        self.assertEqual(self.source.read_bytes(), original)
        self.assertFalse(self.backup.exists())

    def test_apply_saved_preview_offline_and_repeat_is_noop(self):
        original = self.source.read_bytes()
        report = self.generate()
        preview = self.preview.read_bytes()
        self.response.unlink()
        # Intake approvals are deliberately outside the humanize source binding.
        (self.base / "intake-checklist.md").write_text("changed independently", encoding="utf-8")
        run = self.invoke("--apply")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.source.read_bytes(), preview)
        self.assertEqual(self.backup.read_bytes(), original)
        self.assertEqual(json.loads(self.report_path.read_text(encoding="utf-8")),
                         {**report, "applied": True})
        paths = (self.source, self.preview, self.report_path, self.backup)
        snapshot = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
        run = self.invoke("--apply")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(snapshot, [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths])

    def test_apply_preserves_existing_original_backup(self):
        self.backup.write_bytes(b"earlier original")
        self.generate()
        run = self.invoke("--apply")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.backup.read_bytes(), b"earlier original")

    def test_stale_source_rejected(self):
        self.generate()
        self.source.write_bytes(self.source.read_bytes() + b"\n")
        self.assert_failure("SOURCE_MISMATCH")

    def test_modified_preview_rejected(self):
        self.generate()
        self.preview.write_bytes(self.preview.read_bytes() + b"\n")
        self.assert_failure("OUTPUT_MISMATCH")

    def test_source_edit_after_apply_rejected(self):
        self.generate()
        run = self.invoke("--apply")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.source.write_bytes(self.source.read_bytes() + b"\n")
        self.assert_failure("SOURCE_MISMATCH")

    def test_missing_preview_or_report_rejected(self):
        self.assert_failure("PREVIEW_INVALID")
        for path in (self.preview, self.report_path):
            with self.subTest(path=path.name):
                self.generate()
                path.unlink()
                self.assert_failure("PREVIEW_INVALID")

    def test_legacy_or_malformed_report_rejected(self):
        for report in ("not json", "[]", '{"applied": false}',
                       '{"source_sha256": "bad", "output_sha256": "bad", "applied": false}'):
            with self.subTest(report=report):
                self.generate()
                self.report_path.write_text(report, encoding="utf-8")
                self.assert_failure("PREVIEW_INVALID")

    def test_apply_rejects_generation_flags_before_processing_them(self):
        self.generate()
        for args in (("--from-json", str(self.response)), ("--model", "unavailable"),
                     ("--category", "health_food"), ("--timeout", "10"), ("--dry-run",),
                     ("--model=unavailable",), ("--from-json",), ("--timeout", "bad")):
            with self.subTest(args=args):
                self.assert_failure("APPLY_FLAGS", *args)

    def test_apply_rejects_unknown_arguments_without_mutating(self):
        for args in (("--help",), ("unexpected",), ("--aply",), ("--apply",)):
            with self.subTest(args=args):
                self.source.write_text(SOURCE, encoding="utf-8")
                self.generate()
                self.assert_failure("APPLY_FLAGS", *args)

    def fake_codex(self, ok_model: str):
        """ok_model로 부를 때만 응답을 쓰고, 그 외에는 용량 초과로 실패하는 가짜 codex."""
        script = self.bin / "codex"
        script.write_text(
            "#!/bin/bash\n"
            'echo call >> "${0%/*}/calls.log"\n'
            'out=""; model=""\n'
            'while [ $# -gt 0 ]; do case "$1" in -o) out="$2"; shift 2;; -m) model="$2"; shift 2;; *) shift;; esac; done\n'
            f'if [ "$model" != "{ok_model}" ]; then echo "ERROR: Selected model is at capacity" >&2; exit 1; fi\n'
            """printf '%s' '{"cuts":[{"id":"C01","body":["가방에 쏙 담아요"]}]}' > "$out"\n""",
            encoding="utf-8")
        script.chmod(0o755)
        return self.bin / "calls.log"

    def test_capacity_falls_back_and_saves_response(self):
        calls = self.fake_codex("gpt-6-sol")
        self.env["SANGSE_HUMANIZE_FALLBACK_MODELS"] = "gpt-6-sol"
        run = self.invoke("--category", "health_food")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(len(calls.read_text(encoding="utf-8").splitlines()), 2)
        report = json.loads(self.report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["model"], "gpt-6-sol")
        saved = json.loads((self.base / report["response"]).read_text(encoding="utf-8"))
        self.assertEqual(saved["cuts"][0]["body"], ["가방에 쏙 담아요"])

    def test_capacity_without_fallback_fails_after_one_call(self):
        calls = self.fake_codex("never")
        self.env["SANGSE_HUMANIZE_FALLBACK_MODELS"] = ""
        run = self.invoke("--category", "health_food")
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(len(calls.read_text(encoding="utf-8").splitlines()), 1)
        self.assertFalse(self.preview.exists())


if __name__ == "__main__":
    unittest.main()
