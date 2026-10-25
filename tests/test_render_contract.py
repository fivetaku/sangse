"""Real-browser layout regressions; fixtures and screenshots stay in temporary copies."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import TypedDict, cast, final
import unittest


PLUGIN = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN / "skills/sangse/scripts"
FIXTURE = PLUGIN / "examples/punggi-red-ginseng-stick"

MEASURE_JS = r"""
const {pathToFileURL} = require('url');
let pw;
try { pw = require('playwright'); } catch { pw = require('patchright'); }
(async () => {
  let browser;
  try { browser = await pw.chromium.launch({channel: 'chrome', headless: true}); }
  catch { browser = await pw.chromium.launch({headless: true}); }
  try {
    const result = {};
    for (const width of [390, 860]) {
      const page = await browser.newPage({viewport: {width, height: 844}});
      await page.goto(pathToFileURL(process.argv[2]).href, {waitUntil: 'load'});
      result[width] = await page.evaluate(() => {
        const main = document.querySelector('main');
        const cuts = [...document.querySelectorAll('.cutsheet > .cut')].map(cut => ({
          id: cut.id,
          width: cut.getBoundingClientRect().width,
          imageWidth: cut.querySelector('img').getBoundingClientRect().width,
        }));
        const legacy = document.createElement('section');
        legacy.className = 'sec';
        legacy.innerHTML = '<figure></figure>';
        main.append(legacy);
        return {mainWidth: main.getBoundingClientRect().width, cuts,
                legacyWidth: legacy.querySelector('figure').getBoundingClientRect().width};
      });
      await page.close();
    }
    console.log(JSON.stringify(result));
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
"""


class CutWidth(TypedDict):
    id: str
    width: float


class CutImageWidth(CutWidth):
    imageWidth: float


class LayoutMeasurement(TypedDict):
    mainWidth: float
    cuts: list[CutImageWidth]
    legacyWidth: float


class RenderMetrics(TypedDict):
    mainWidth: float
    cutsFillMainWidth: bool
    cutWidths: list[float]
    cutWidthMismatches: list[CutWidth]
    imageWidthMismatches: list[CutWidth]
    brokenImages: int
    requestFailed: list[str]
    closingCutPresent: bool
    ctaPositionStatus: str
    firstCtaTop: float | None
    ctaInFirstTwoViewports: bool | None


class RenderCheck(TypedDict):
    width: int
    status: str
    metrics: RenderMetrics
    fails: list[str]


class RenderReport(TypedDict):
    verdict: str
    checks: list[RenderCheck]


@final
class RenderContractTests(unittest.TestCase):
    def __init__(self, methodName: str = "runTest"):
        super().__init__(methodName)
        tmp = tempfile.TemporaryDirectory(prefix="sangse-render-test-")
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        _ = shutil.copytree(FIXTURE, self.base, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("qa", "index.html", "legacy-v0.3"))
        assembled = subprocess.run(
            [sys.executable, str(SCRIPTS / "assemble_html.py"), str(self.base)],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(assembled.returncode, 0, assembled.stderr)
        self.assertEqual(json.loads(assembled.stdout)["missing_images"], [])

    def render_check(self):
        run = subprocess.run(
            [sys.executable, str(SCRIPTS / "render_check.py"), str(self.base),
             "--widths", "390,860"], capture_output=True, text=True, timeout=90)
        report_path = self.base / "qa/render_check.json"
        self.assertTrue(report_path.exists(), run.stdout + run.stderr)
        return run, cast(RenderReport, json.loads(report_path.read_text(encoding="utf-8")))

    def test_assembled_cuts_fill_main_at_mobile_and_desktop(self):
        js = self.base / "measure.js"
        _ = js.write_text(MEASURE_JS, encoding="utf-8")
        env = dict(os.environ)
        paths = [p for p in [env.get("SANGSE_NODE_MODULES"),
                            str(Path.home() / ".insane-search/node/node_modules"),
                            env.get("NODE_PATH")] if p]
        env["NODE_PATH"] = os.pathsep.join(paths)
        run = subprocess.run(["node", str(js), str(self.base / "index.html")],
                             env=env, capture_output=True, text=True, timeout=90)
        self.assertEqual(run.returncode, 0, run.stderr)
        measurements = cast(dict[str, LayoutMeasurement], json.loads(run.stdout))
        for viewport, metrics in measurements.items():
            with self.subTest(viewport=viewport):
                self.assertEqual(metrics["mainWidth"], int(viewport))
                self.assertEqual(len(metrics["cuts"]), 14)
                self.assertEqual(metrics["legacyWidth"], min(int(viewport), 400))
                self.assertEqual([cut["width"] for cut in metrics["cuts"]],
                                 [metrics["mainWidth"]] * 14)
                self.assertEqual([cut["imageWidth"] for cut in metrics["cuts"]],
                                 [metrics["mainWidth"]] * 14)

    def test_render_gate_measures_every_cut_with_lazy_images(self):
        index = self.base / "index.html"
        source = index.read_text(encoding="utf-8")
        _ = index.write_text(source.replace('<img ', '<img loading="lazy" '), encoding="utf-8")
        run, report = self.render_check()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(report["verdict"], "PASS")
        for check in report["checks"]:
            metrics = check["metrics"]
            self.assertEqual(metrics["mainWidth"], check["width"])
            self.assertTrue(metrics["cutsFillMainWidth"])
            self.assertEqual(metrics["cutWidths"], [check["width"]] * 14)
            self.assertEqual(metrics["cutWidthMismatches"], [])
            self.assertEqual(metrics["brokenImages"], 0)
            self.assertEqual(metrics["requestFailed"], [])

    def test_render_gate_reports_lazy_image_error(self):
        index = self.base / "index.html"
        source = index.read_text(encoding="utf-8")
        _ = index.write_text(source.replace('<img ', '<img loading="lazy" ')
                             .replace('images/c14.png', 'images/missing.png'), encoding="utf-8")
        run, report = self.render_check()
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        for check in report["checks"]:
            self.assertEqual(check["status"], "FAIL")
            self.assertEqual(check["metrics"]["brokenImages"], 1)
            self.assertTrue(check["metrics"]["cutsFillMainWidth"])
            self.assertEqual(len(check["metrics"]["requestFailed"]), 1)

    def test_render_gate_rejects_narrow_nonfirst_cut(self):
        index = self.base / "index.html"
        source = index.read_text(encoding="utf-8")
        _ = index.write_text(source.replace('</style>', '#c02 { max-width: 200px; }</style>'),
                             encoding="utf-8")
        run, report = self.render_check()
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        self.assertEqual(report["verdict"], "FAIL")
        for check in report["checks"]:
            self.assertEqual(check["status"], "FAIL")
            metrics = check["metrics"]
            self.assertEqual(metrics["cutWidths"][0], check["width"])
            self.assertEqual(metrics["cutWidths"][1], 200)
            self.assertFalse(metrics["cutsFillMainWidth"])
            self.assertEqual(metrics["cutWidthMismatches"], [{"id": "c02", "width": 200}])
            self.assertTrue(check["fails"])

    def test_cut_presence_does_not_claim_measured_cta_position(self):
        run, report = self.render_check()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        for check in report["checks"]:
            metrics = check["metrics"]
            self.assertTrue(metrics["closingCutPresent"])
            self.assertEqual(metrics["ctaPositionStatus"], "manual_review")
            self.assertIsNone(metrics["firstCtaTop"])
            self.assertIsNone(metrics["ctaInFirstTwoViewports"])

    def test_render_gate_rejects_narrow_image_inside_full_width_cut(self):
        index = self.base / "index.html"
        source = index.read_text(encoding="utf-8")
        _ = index.write_text(source.replace('</style>', '#c02 img { width: 200px; }</style>'),
                             encoding="utf-8")
        run, report = self.render_check()
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        for check in report["checks"]:
            metrics = check["metrics"]
            self.assertEqual(metrics["cutWidths"], [check["width"]] * 14)
            self.assertEqual(metrics["cutWidthMismatches"], [])
            self.assertEqual(metrics["imageWidthMismatches"], [{"id": "c02", "width": 200}])
            self.assertFalse(metrics["cutsFillMainWidth"])

    def test_render_gate_rejects_small_or_low_contrast_text(self):
        run, report = self.render_check()
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        for check in report["checks"]:
            self.assertEqual(check["metrics"]["textIssues"], [])
            self.assertGreater(check["metrics"]["textChecked"], 0)
            self.assertEqual(len(check["metrics"]["cutImageScale"]), 14)
            # 브리프(image-briefs §3)는 폭 1000 기준이다 — 390에서 36px, 860에서 17px가 14px로 보인다
            per1000 = {s["px1000For14"] for s in check["metrics"]["cutImageScale"]}
            self.assertEqual(per1000, {36 if check["width"] == 390 else 17}, per1000)
        index = self.base / "index.html"
        source = index.read_text(encoding="utf-8")
        _ = index.write_text(source.replace(
            '</style>', '.legal td { color: #bbb; } footer { font-size: 11px; }</style>'), encoding="utf-8")
        run, report = self.render_check()
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        for check in report["checks"]:
            self.assertEqual(check["status"], "FAIL")
            issues = check["metrics"]["textIssues"]
            self.assertTrue(any(i["selector"] == "td" and i["contrast"] < 4.5 for i in issues), issues)
            self.assertTrue(any(i["selector"] == "footer" and i["fontSize"] == 11 for i in issues), issues)

    def test_cut_gate_rejects_missing_closing_cut(self):
        index = self.base / "index.html"
        source = index.read_text(encoding="utf-8")
        _ = index.write_text(source.replace('data-q="Q7"', 'data-q="Q6"')
                             .replace('data-q="Q8"', 'data-q="Q6"'), encoding="utf-8")
        run, report = self.render_check()
        self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
        for check in report["checks"]:
            self.assertFalse(check["metrics"]["closingCutPresent"])

    def test_text_mode_still_measures_actual_cta_position(self):
        index = self.base / "index.html"
        for top, expected in ((40, True), (2000, False)):
            with self.subTest(top=top):
                _ = index.write_text(
                    '<html><head><meta name="viewport" content="width=device-width">'
                    '</head><body><main><section id="q1"><h2>Product</h2></section>'
                    f'<a class="cta" style="position:absolute;top:{top}px" href="#buy">'
                    'Buy</a></main></body></html>', encoding="utf-8")
                run, report = self.render_check()
                self.assertEqual(run.returncode, 0 if expected else 1, run.stdout + run.stderr)
                for check in report["checks"]:
                    metrics = check["metrics"]
                    self.assertEqual(metrics["ctaPositionStatus"], "measured")
                    self.assertEqual(metrics["firstCtaTop"], top)
                    self.assertEqual(metrics["ctaInFirstTwoViewports"], expected)


if __name__ == "__main__":
    _ = unittest.main()
