"""Offline tests: a local mock of every supported provider. No network, no real keys."""

import base64
import contextlib
import io
import json
import os
import re
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

SKILL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills", "seedream-5-5")
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))
import seedream  # noqa: E402

FAKE_KEY = "test-key-0123456789abcdef"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
B64 = base64.b64encode(PNG).decode()


class Mock(BaseHTTPRequestHandler):
    """Routes are prefixed with the provider name, e.g. /fal/..., so one server serves all."""
    log = []          # (method, path, auth header, body)
    mode = "ok"
    polls = {}

    def log_message(self, *a):
        pass

    def _send(self, code, obj, raw=None, ctype="application/json"):
        body = raw if raw is not None else json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _record(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n)) if n else None
        Mock.log.append((self.command, self.path, self.headers.get("Authorization"), body))
        return body

    def base(self):
        return "http://127.0.0.1:{}".format(self.server.server_port)

    def _pending_once(self, key):
        """Return True the first time a poll key is seen, so every async flow polls twice."""
        Mock.polls[key] = Mock.polls.get(key, 0) + 1
        return Mock.polls[key] == 1

    def do_GET(self):
        self._record()
        p, b = self.path, self.base()
        if p == "/cdn/img.png":
            return self._send(200, None, raw=PNG, ctype="image/png")
        if p.startswith("/ark/models"):
            return self._send(200, {"data": [{"id": "dola-seedream-5-5-261028"}, {"id": "seedance-x"}]})
        if p.startswith("/ws/predictions/"):
            st = "processing" if self._pending_once(p) else "completed"
            return self._send(200, {"data": {"status": st, "outputs": [b + "/cdn/img.png"]}})
        if p.startswith("/kie/jobs/recordInfo"):
            st = "generating" if self._pending_once(p) else "success"
            return self._send(200, {"code": 200, "data": {"state": st, "resultJson": json.dumps(
                {"resultUrls": [b + "/cdn/img.png"]})}})
        if p.startswith("/evo/tasks/"):
            st = "processing" if self._pending_once(p) else "completed"
            return self._send(200, {"status": st, "results": [b + "/cdn/img.png"]})
        if p.startswith("/fal/status"):
            st = "IN_PROGRESS" if self._pending_once(p) else "COMPLETED"
            return self._send(200, {"status": st})
        if p.startswith("/fal/response"):
            if any(e[0] == "POST" and e[1].endswith("/layerize") for e in Mock.log):
                img = {"url": b + "/cdn/img.png", "width": 200, "height": 100}
                return self._send(200, {"layers": [
                    {"image": dict(img, width=400, height=300), "z_index": 0},
                    {"image": img, "z_index": 1, "name": "Hello text",
                     "bounding_box": {"absolute": [10, 20, 110, 70], "normalized": [25, 66, 275, 233]},
                     "text_recognition": {"text": "HELLO", "lines": []}}],
                    "images": [{"url": b + "/cdn/img.png"}, {"url": b + "/cdn/img.png"}]})
            return self._send(200, {"images": [{"url": b + "/cdn/img.png"}], "seed": 7})
        if p.startswith("/rep/get"):
            st = "processing" if self._pending_once(p) else "succeeded"
            return self._send(200, {"id": "r1", "status": st, "output": [b + "/cdn/img.png"]})
        self._send(404, {"error": "no route " + p})

    def do_POST(self):
        self._record()
        p, b = self.path, self.base()
        body = Mock.log[-1][3] or {}
        if Mock.mode == "error":
            return self._send(401, {"error": {"message": "bad token " + self.headers.get("Authorization", "")}})
        if p == "/ark/images/generations" and body.get("layer_decomposition"):
            text = {"text": "SALE", "lines": [{"runs": [{"text": "SALE", "style": {"foreground_color": "#FFFFFF"}}]}]}
            return self._send(200, {"usage": {"generated_images": 3}, "data": [
                {"b64_json": B64, "size": "1000x1500", "z_index": 0, "background": "opaque"},
                {"b64_json": B64, "size": "2000x400", "z_index": 1, "name": "Headline SALE",
                 "bounding_box": {"absolute": [100, 50, 900, 210], "normalized": [100, 33, 900, 140]},
                 "text_recognition": text, "background": "transparent"},
                {"b64_json": B64, "size": "1200x1200", "z_index": 2, "name": "Red shoe",
                 "bounding_box": {"absolute": [300, 600, 700, 1000]}, "background": "transparent"}]})
        if p == "/ark/images/generations":
            return self._send(200, {"created": 1, "usage": {"generated_images": 1},
                                    "data": [{"b64_json": B64, "size": "2560x1440"}]})
        if p == "/runware":
            return self._send(200, {"data": [{"imageBase64Data": B64, "seed": 42, "cost": 0.035}]})
        if p.startswith("/ws/bytedance/"):
            return self._send(200, {"data": {"id": "w1"}})
        if p == "/kie/jobs/createTask":
            return self._send(200, {"code": 200, "data": {"taskId": "k1"}})
        if p == "/evo/images/generations":
            return self._send(200, {"id": "e1", "status": "pending"})
        if p.startswith("/fal/bytedance/"):
            return self._send(200, {"request_id": "f1", "status_url": b + "/fal/status/f1",
                                    "response_url": b + "/fal/response/f1"})
        if p.startswith("/rep/models/"):
            return self._send(201, {"id": "r1", "status": "starting", "urls": {"get": b + "/rep/get/r1"}})
        if p == "/or/images":
            return self._send(200, {"data": [{"b64_json": B64}]})
        self._send(404, {"error": "no route " + p})


ROUTE = {"byteplus": "/ark", "volcengine": "/ark", "runware": "/runware", "wavespeed": "/ws",
         "kie": "/kie", "evolink": "/evo", "fal": "/fal", "replicate": "/rep", "openrouter": "/or"}


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Mock)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.root = "http://127.0.0.1:{}".format(cls.srv.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        Mock.mode, Mock.log, Mock.polls = "ok", [], {}
        for p in seedream.PROVIDERS.values():
            os.environ[p["env"]] = FAKE_KEY
        self.tmp = tempfile.mkdtemp()

    def run_cli(self, provider, *argv, cmd="generate"):
        out, err = io.StringIO(), io.StringIO()
        full = [cmd, "--provider", provider, "--base-url", self.root + ROUTE[provider]]
        if cmd == "generate":
            full += ["--poll-interval", "0"]
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = seedream.main(full + list(argv))
        return code, out.getvalue(), err.getvalue()

    def written(self):
        blob = b""
        for root, _, files in os.walk(self.tmp):
            for f in files:
                with open(os.path.join(root, f), "rb") as fh:
                    blob += fh.read()
        return blob

    def first_post(self):
        return next(e for e in Mock.log if e[0] == "POST")


class EveryProvider(Base):
    def test_each_provider_end_to_end(self):
        for provider in ROUTE:
            with self.subTest(provider=provider):
                Mock.log, Mock.polls = [], {}
                out_dir = os.path.join(self.tmp, provider)
                code, out, err = self.run_cli(provider, "--prompt", "A harbour at dawn.",
                                              "--size", "16:9", "--out", out_dir, "--name", "x")
                self.assertEqual(code, 0, err)
                with open(os.path.join(out_dir, "x.png"), "rb") as f:
                    self.assertEqual(f.read(), PNG)
                with open(os.path.join(out_dir, "x.txt"), encoding="utf-8") as f:
                    side = f.read()
                self.assertIn("provider: " + provider, side)
                self.assertIn("A harbour at dawn.", side)
                self.assertNotIn(FAKE_KEY, out + err + side)

                expected = "Key " + FAKE_KEY if provider == "fal" else "Bearer " + FAKE_KEY
                api_calls = [e for e in Mock.log if not e[1].startswith("/cdn/")]
                self.assertTrue(all(e[2] == expected for e in api_calls), api_calls)
                # Result images on a CDN must be fetched WITHOUT credentials.
                for e in Mock.log:
                    if e[1].startswith("/cdn/"):
                        self.assertIsNone(e[2], "API key sent to image CDN")

    def test_async_providers_actually_poll(self):
        for provider in ("wavespeed", "kie", "evolink", "fal", "replicate"):
            with self.subTest(provider=provider):
                Mock.log, Mock.polls = [], {}
                code, _, err = self.run_cli(provider, "--prompt", "x", "--out", self.tmp)
                self.assertEqual(code, 0, err)
                self.assertTrue(any(v >= 2 for v in Mock.polls.values()), Mock.polls)


class RequestShapes(Base):
    def body(self, provider, *argv):
        code, out, err = self.run_cli(provider, "--prompt", "p", "--dry-run", *argv)
        self.assertEqual(code, 0, err)
        return json.loads(out)["request"]

    def test_byteplus(self):
        b = self.body("byteplus", "--size", "2:3", "--background", "transparent")
        self.assertEqual(b["model"], "dola-seedream-5-5-261028")
        self.assertEqual(b["size"], "1728x2592")
        self.assertEqual(b["response_format"], "b64_json")
        self.assertIs(b["watermark"], False)
        self.assertEqual(b["background"], "transparent")
        self.assertEqual(self.body("byteplus", "--size", "1.5K")["size"], "1.5K")

    def test_volcengine_model(self):
        self.assertEqual(self.body("volcengine")["model"], "doubao-seedream-5-5-261028")

    def test_runware(self):
        t = self.body("runware", "--size", "1:1")[0]
        self.assertEqual((t["width"], t["height"]), (2048, 2048))
        self.assertEqual(t["model"], "bytedance:seedream@5.5")
        self.assertEqual(self.body("runware", "--size", "2K")[0]["resolution"], "2K")

    def test_wavespeed_switches_to_edit_with_images(self):
        ref = os.path.join(self.tmp, "r.png")
        with open(ref, "wb") as f: f.write(PNG)
        code, out, _ = self.run_cli("wavespeed", "--prompt", "p", "--image", ref, "--dry-run")
        d = json.loads(out)
        self.assertTrue(d["url"].endswith("/bytedance/seedream-v5.5/edit"))
        self.assertEqual(d["request"]["aspect_ratio"], "16:9")
        self.assertEqual(d["request"]["resolution"], "2k")

    def test_kie_and_evolink_need_urls(self):
        ref = os.path.join(self.tmp, "r.png")
        with open(ref, "wb") as f: f.write(PNG)
        for provider in ("kie", "evolink"):
            code, _, err = self.run_cli(provider, "--prompt", "p", "--image", ref, "--dry-run")
            self.assertEqual(code, 1)
            self.assertIn("public image URLs", err)
        b = self.body("kie", "--image", "https://example.com/a.png")
        self.assertEqual(b["model"], "seedream/5-5-image-to-image")
        self.assertEqual(b["input"]["image_urls"], ["https://example.com/a.png"])

    def test_fal_replicate_openrouter(self):
        self.assertEqual(self.body("fal", "--size", "3:2")["image_size"], {"width": 2592, "height": 1728})
        self.assertEqual(self.body("replicate", "--size", "9:16")["input"]["aspect_ratio"], "9:16")
        o = self.body("openrouter", "--image", "https://e.com/a.png")
        self.assertEqual(o["input_references"][0]["image_url"]["url"], "https://e.com/a.png")

    def test_ratio_only_provider_rejects_odd_size(self):
        code, _, err = self.run_cli("wavespeed", "--prompt", "p", "--size", "1500x1000", "--dry-run")
        self.assertEqual(code, 0)  # 3:2 exactly
        code, _, err = self.run_cli("wavespeed", "--prompt", "p", "--size", "1700x1000", "--dry-run")
        self.assertEqual(code, 1)
        self.assertIn("named aspect ratios", err)

    def test_inline_image_never_dumped(self):
        ref = os.path.join(self.tmp, "r.png")
        with open(ref, "wb") as f: f.write(PNG * 10)
        code, out, _ = self.run_cli("byteplus", "--prompt", "p", "--image", ref, "--dry-run")
        self.assertNotIn("base64,", out)
        self.assertIn("sha256", out)
        self.assertNotIn(os.path.abspath(self.tmp).replace("\\", "/"), out)


class Safety(Base):
    def test_error_text_is_scrubbed(self):
        Mock.mode = "error"
        for provider in ("byteplus", "fal"):
            code, out, err = self.run_cli(provider, "--prompt", "x", "--out", self.tmp)
            self.assertEqual(code, 1)
            self.assertIn("HTTP 401", err)
            self.assertNotIn(FAKE_KEY, out + err)

    def test_missing_key_names_the_right_variable(self):
        del os.environ["FAL_KEY"]
        code, _, err = self.run_cli("fal", "--prompt", "x", "--out", self.tmp)
        self.assertEqual(code, 1)
        self.assertIn("FAL_KEY is not set", err)

    def test_dry_run_needs_no_key(self):
        for p in seedream.PROVIDERS.values():
            os.environ.pop(p["env"], None)
        code, out, _ = self.run_cli("replicate", "--prompt", "x", "--dry-run")
        self.assertEqual(code, 0)

    def test_no_overwrite(self):
        for _ in range(2):
            self.assertEqual(self.run_cli("byteplus", "--prompt", "x", "--out", self.tmp, "--name", "a")[0], 0)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "a_2.png")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "a_2.txt")))

    def test_models_listing(self):
        code, out, _ = self.run_cli("byteplus", cmd="models")
        self.assertEqual(code, 0)
        self.assertIn("dola-seedream-5-5-261028", out)
        self.assertNotIn("seedance", out)


class Validation(unittest.TestCase):
    def test_size_limits(self):
        self.assertEqual(seedream.parse_size("2:3"), ("wh", (1728, 2592)))
        self.assertEqual(seedream.parse_size("21:9"), ("wh", (3024, 1296)))
        self.assertEqual(seedream.parse_size("1280x720"), ("wh", (1280, 720)))   # exactly the minimum
        self.assertEqual(seedream.parse_size("2k"), ("tier", "2K"))
        for bad in ("1024x768", "4096x4096", "banana"):
            with self.assertRaises(seedream.HelperError):
                seedream.parse_size(bad)

    def test_presets_within_limits(self):
        for r, wh in seedream.SIZE_PRESETS.items():
            w, h = map(int, wh.split("x"))
            self.assertTrue(seedream.MIN_AREA <= w * h <= seedream.MAX_AREA, r)
            self.assertAlmostEqual(w / h, seedream.eval_ratio(r), places=2)

    def test_reference_limit_and_transparency(self):
        with self.assertRaises(SystemExit):
            pass_through = seedream.main(["generate", "--prompt", "x", "--dry-run",
                                          "--background", "transparent", "--output-format", "jpeg"])
            raise SystemExit(pass_through)


class Options(Base):
    def test_count_makes_n_options_and_a_sheet(self):
        for provider in ("byteplus", "wavespeed"):
            with self.subTest(provider=provider):
                Mock.log, Mock.polls = [], {}
                out_dir = os.path.join(self.tmp, provider)
                code, out, err = self.run_cli(provider, "--prompt", "x", "--count", "3",
                                              "--out", out_dir, "--name", "opt")
                self.assertEqual(code, 0, err)
                files = sorted(os.listdir(out_dir))
                for i in (1, 2, 3):
                    self.assertIn("opt_{}.png".format(i), files)
                    self.assertIn("opt_{}.txt".format(i), files)
                self.assertIn("opt_sheet.html", files)
                posts = [e for e in Mock.log if e[0] == "POST"]
                self.assertEqual(len(posts), 3)
                with open(os.path.join(out_dir, "opt_sheet.html"), encoding="utf-8") as f:
                    sheet = f.read()
                self.assertIn("opt_2.png", sheet)
                self.assertNotIn(FAKE_KEY, sheet)

    def test_count_cap(self):
        code, _, err = self.run_cli("byteplus", "--prompt", "x", "--count", "9", "--out", self.tmp)
        self.assertEqual(code, 1)
        self.assertIn("capped at 8", err)


class Layers(Base):
    def test_layers_request_and_files(self):
        src = os.path.join(self.tmp, "poster.png")
        with open(src, "wb") as f:
            f.write(PNG)
        out_dir = os.path.join(self.tmp, "out")
        code, out, err = self.run_cli("byteplus", "--prompt", "Split into layers", "--image", src,
                                      "--layers", "5", "--ocr", "--size", "2K", "--out", out_dir, "--name", "poster")
        self.assertEqual(code, 0, err)
        body = self.first_post()[3]
        self.assertTrue(body["layer_decomposition"])
        self.assertEqual(body["layer_decomposition_options"], {"max_images": 5, "text_recognition": True})
        self.assertNotIn("background", body)
        folder = os.path.join(out_dir, "poster_layers")
        files = sorted(os.listdir(folder))
        self.assertEqual(files, ["00_base.png", "01_sale.png", "02_red_shoe.png", "layers.json", "viewer.html"])
        with open(os.path.join(folder, "layers.json"), encoding="utf-8") as f:
            man = json.load(f)
        self.assertEqual(man["canvas"], [1000, 1500])
        self.assertEqual(man["layers"][1]["box"], [100, 50, 900, 210])
        self.assertEqual(man["layers"][1]["text"], "SALE")
        self.assertIn("billed images: 3", out)
        self.assertNotIn(FAKE_KEY.encode(), self.written())

    def test_layer_saver_edge_cases(self):
        resp = {"data": [
            {"b64_json": B64, "size": "400x300", "z_index": 0},
            {"b64_json": B64, "size": "10x10", "z_index": 1, "name": "</script><b>x",
             "bounding_box": {"absolute": [0, 0, 10, 10]}},
            {"b64_json": B64, "size": "10x10", "z_index": 1, "name": "twin",
             "bounding_box": {"absolute": [5, 5, 15, 15]}},
            {"z_index": 2, "name": "empty"}]}
        spec = {"model": "m", "prompt": "p"}
        summ = {"request": {"model": "m"}, "reference_images": []}
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            files = seedream.save_layers(self.tmp, "e", resp, "byteplus", spec, summ, {})
        self.assertEqual(len(files), 3)                       # twin z_index kept, empty one skipped
        self.assertEqual(len(set(files)), 3)
        self.assertIn("skipped", err.getvalue())
        with open(os.path.join(self.tmp, "e_layers", "viewer.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertNotIn("</script><b>", page)
        with open(os.path.join(self.tmp, "e_layers", "layers.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["canvas"], [400, 300])

    def test_layers_validation(self):
        for argv, msg in ((["--layers", "5"], "exactly one image"),
                          (["--layers", "1", "--image", "a.png"], "2-100"),
                          (["--layers", "5", "--image", "a.png", "--background", "transparent"], "cannot be combined")):
            with self.subTest(argv=argv):
                src = os.path.join(self.tmp, "a.png")
                with open(src, "wb") as f:
                    f.write(PNG)
                argv = [src if a == "a.png" else a for a in argv]
                code, _, err = self.run_cli("byteplus", "--prompt", "x", "--dry-run", *argv)
                self.assertEqual(code, 1)
                self.assertIn(msg, err)
        code, _, err = self.run_cli("kie", "--prompt", "x", "--image", "https://x/a.png", "--layers", "4", "--dry-run")
        self.assertIn("--extra", err)

    def test_fal_layerize(self):
        out_dir = os.path.join(self.tmp, "out")
        code, out, err = self.run_cli("fal", "--prompt", "Split", "--image", "https://x/a.png", "--layers", "6",
                                      "--ocr", "--size", "2K", "--out", out_dir, "--name", "p")
        self.assertEqual(code, 0, err)
        post = self.first_post()
        self.assertTrue(post[1].endswith("/bytedance/seedream/v5.5/layerize"))
        self.assertEqual(post[3]["max_images"], 6)
        self.assertTrue(post[3]["enable_text_recognition"])
        self.assertEqual(post[3]["image_url"], "https://x/a.png")
        files = sorted(os.listdir(os.path.join(out_dir, "p_layers")))
        self.assertEqual(files, ["00_base.png", "01_hello.png", "layers.json", "viewer.html"])
        with open(os.path.join(out_dir, "p_layers", "layers.json"), encoding="utf-8") as f:
            man = json.load(f)
        self.assertEqual(man["layers"][1]["box"], [10, 20, 110, 70])


class Batch(Base):
    def manifest(self, extra_asset=None):
        style = os.path.join(self.tmp, "style.md")
        with open(style, "w", encoding="utf-8") as f:
            f.write("flat risograph look")
        assets = [{"name": "hero", "prompt": "a hero", "size": "16:9"},
                  {"name": "card", "prompt": "a card", "size": "2K"}]
        if extra_asset:
            assets.append(extra_asset)
        man = {"provider": "byteplus", "out": "out", "style_file": "style.md", "assets": assets}
        path = os.path.join(self.tmp, "assets.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(man, f)
        return path

    def run_batch(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = seedream.main(["batch"] + list(argv) + ["--base-url", self.root + "/ark", "--poll-interval", "0"])
        return code, out.getvalue(), err.getvalue()

    def test_plan_needs_yes_then_runs_then_skips(self):
        m = self.manifest()
        code, out, _ = self.run_batch(m)
        self.assertEqual(code, 3)
        self.assertIn("~$0.07 for 2 images", out)
        self.assertFalse([e for e in Mock.log if e[0] == "POST"])          # nothing spent
        code, out, err = self.run_batch(m, "--yes")
        self.assertEqual(code, 0, err)
        posts = [e for e in Mock.log if e[0] == "POST"]
        self.assertEqual(len(posts), 2)
        self.assertTrue(all("House style for this project: flat risograph look" in e[3]["prompt"] for e in posts))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "out", "hero.png")))
        Mock.log = []
        code, out, _ = self.run_batch(m, "--yes")
        self.assertEqual(code, 0)
        self.assertIn("2 up to date", out)
        self.assertFalse([e for e in Mock.log if e[0] == "POST"])
        # changing one prompt regenerates only that asset
        with open(m, encoding="utf-8") as f:
            man = json.load(f)
        man["assets"][1]["prompt"] = "a different card"
        with open(m, "w", encoding="utf-8") as f:
            json.dump(man, f)
        code, out, _ = self.run_batch(m, "--yes")
        self.assertIn("1 up to date, 1 to generate", out)
        self.assertEqual(len([e for e in Mock.log if e[0] == "POST"]), 1)
        out_files = sorted(os.listdir(os.path.join(self.tmp, "out")))
        self.assertEqual(out_files, ["card.png", "hero.png"])              # same names, no card_2.png
        self.assertTrue(os.path.isdir(os.path.join(self.tmp, ".seedream", "replaced")))   # old one kept aside
        with open(os.path.join(self.tmp, ".seedream", "state", "card.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["files"], ["out/card.png"])        # relative, no user paths
        self.assertNotIn(FAKE_KEY.encode(), self.written())

    def test_costs_ledger(self):
        m = self.manifest()
        self.run_batch(m, "--yes")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            seedream.main(["costs", "--out", os.path.join(self.tmp, ".seedream")])
        self.assertIn("2 calls", out.getvalue())
        self.assertIn("~$0.070", out.getvalue())
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "out", "hero.txt")))   # records kept out of out/
        self.assertTrue(os.path.exists(os.path.join(self.tmp, ".seedream", "records", "hero.txt")))
        with open(os.path.join(self.tmp, ".seedream", ".seedream-ledger.jsonl"), encoding="utf-8") as f:
            ledger = f.read()
        self.assertNotIn("a hero", ledger)                                 # no prompts in the ledger

    def test_bad_names_rejected(self):
        for bad in ("../evil", "-x", "..", "CON"):
            m = self.manifest({"name": bad, "prompt": "x"})
            code, _, err = self.run_batch(m, "--dry-run")
            self.assertEqual(code, 1, bad)
            self.assertIn("name", err)

    def test_manifest_in_dot_seedream_resolves_from_project_root(self):
        os.makedirs(os.path.join(self.tmp, ".seedream"))
        with open(os.path.join(self.tmp, ".seedream", "style.md"), "w", encoding="utf-8") as f:
            f.write("ink wash")
        man = {"out": "public/images", "style_file": ".seedream/style.md",
               "assets": [{"name": "hero", "prompt": "a hero"}]}
        m = os.path.join(self.tmp, ".seedream", "assets.json")
        with open(m, "w", encoding="utf-8") as f:
            json.dump(man, f)
        code, out, err = self.run_batch(m, "--yes")
        self.assertEqual(code, 0, err)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "public", "images", "hero.png")))

    def test_bad_final_size_fails_before_spending(self):
        m = self.manifest({"name": "x", "prompt": "x", "final_size": "1200by630"})
        code, _, err = self.run_batch(m, "--yes")
        self.assertEqual(code, 1)
        self.assertIn("1200x630", err)
        self.assertFalse([e for e in Mock.log if e[0] == "POST"])

    def test_dry_run_reports_cost(self):
        code, out, _ = self.run_cli("byteplus", "--prompt", "x", "--size", "1K", "--image", "https://x/a.png", "--dry-run")
        self.assertIn('"estimated_cost_usd": 0.028', out)
        code, out, _ = self.run_cli("byteplus", "--prompt", "x", "--image", "https://x/a.png", "--image", "https://x/b.png",
                                    "--count", "4", "--dry-run")
        self.assertIn('"estimated_cost_usd": 0.204', out)                    # inputs re-sent on every call
        code, out, _ = self.run_cli("fal", "--prompt", "x", "--dry-run")
        self.assertIn("unknown for this platform", out)


try:
    from PIL import Image as _PIL
except ImportError:      # export.py needs Pillow; the generator doesn't
    _PIL = None
import export  # noqa: E402


@unittest.skipIf(_PIL is None, "Pillow not installed")
class Export(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def img(self, name, size=(2560, 1440), color=(40, 80, 120), mode="RGB"):
        p = os.path.join(self.tmp, name)
        _PIL.new(mode, size, color).save(p)
        return p

    def run_export(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = export.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_presets_crop_to_exact_size(self):
        src = self.img("a.png")
        code, out, err = self.run_export(src, "--to", "instagram-post", "--to", "story", "--to", "youtube-thumb")
        self.assertEqual(code, 0, err)
        for label, wh in (("instagram-post", (1080, 1350)), ("story", (1080, 1920)), ("youtube-thumb", (1280, 720))):
            self.assertEqual(_PIL.open(os.path.join(self.tmp, "a_{}.jpg".format(label))).size, wh)
        self.assertIn("trims", err)           # 16:9 -> 4:5 loses a lot; must warn

    def test_pad_keeps_transparency(self):
        src = self.img("t.png", (1000, 1000), (255, 0, 0, 0), mode="RGBA")
        code, _, err = self.run_export(src, "--size", "1600x900", "--fit", "pad", "--pad-color", "transparent")
        self.assertEqual(code, 0, err)
        im = _PIL.open(os.path.join(self.tmp, "t_1600x900.png"))
        self.assertEqual(im.mode, "RGBA")
        self.assertEqual(im.getpixel((5, 5))[3], 0)

    def test_flip_mirrors(self):
        p = os.path.join(self.tmp, "f.png")
        im = _PIL.new("RGB", (100, 50), (0, 0, 0))
        im.paste((255, 255, 255), (0, 0, 10, 50))            # white strip on the left
        im.save(p)
        code, _, _ = self.run_export(p, "--flip")
        self.assertEqual(code, 0)
        out = _PIL.open(os.path.join(self.tmp, "f_flipped.jpg")).convert("RGB")
        self.assertGreater(out.getpixel((95, 25))[0], 200)    # now on the right
        self.assertLess(out.getpixel((5, 25))[0], 50)

    def test_merge_keeps_untouched_pixels_original(self):
        orig = os.path.join(self.tmp, "orig.png")
        edit = os.path.join(self.tmp, "edit.png")
        a = _PIL.new("RGB", (1200, 800), (100, 100, 100))
        b = a.copy()
        b = b.point(lambda v: min(255, v + 2))               # global re-render noise
        b.paste((220, 30, 30), (500, 300, 700, 450))           # the real edit
        a.save(orig)
        b.save(edit)
        code, out, err = self.run_export("merge", orig, edit, "--save-mask")
        self.assertEqual(code, 0, err)
        m = _PIL.open(os.path.join(self.tmp, "edit_merged.png")).convert("RGB")
        self.assertEqual(m.getpixel((50, 50)), (100, 100, 100))      # untouched area = original
        self.assertEqual(m.getpixel((600, 375)), (220, 30, 30))      # edited area = edit
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "edit_mask.png")))


@unittest.skipIf(_PIL is None, "Pillow not installed")
class LayerTools(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def run_export(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = export.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_layers_assemble_to_canvas(self):
        folder = os.path.join(self.tmp, "x_layers")
        os.makedirs(folder)
        _PIL.new("RGBA", (400, 300), (0, 0, 255, 255)).save(os.path.join(folder, "00_base.png"))
        _PIL.new("RGBA", (200, 100), (255, 0, 0, 255)).save(os.path.join(folder, "01_box.png"))   # 2x crop
        man = {"canvas": [400, 300], "layers": [
            {"z_index": 0, "file": "00_base.png", "box": [0, 0, 400, 300]},
            {"z_index": 1, "file": "01_box.png", "box": [50, 60, 150, 110], "name": "box"}]}
        with open(os.path.join(folder, "layers.json"), "w") as f:
            json.dump(man, f)
        code, out, err = self.run_export("layers", folder)
        self.assertEqual(code, 0, err)
        comp = _PIL.open(os.path.join(folder, "composite.png")).convert("RGB")
        self.assertEqual(comp.getpixel((100, 85)), (255, 0, 0))
        self.assertEqual(comp.getpixel((10, 10)), (0, 0, 255))
        aligned = _PIL.open(os.path.join(folder, "aligned", "01_box.png"))
        self.assertEqual(aligned.size, (400, 300))
        self.assertEqual(aligned.getpixel((10, 10))[3], 0)
        with open(os.path.join(folder, "layers.svg"), encoding="utf-8") as f:
            svg = f.read()
        self.assertEqual(svg.count("<image "), 2)
        self.assertIn('x="50" y="60" width="100" height="50"', svg)

    def test_layers_live_text_and_original_size(self):
        folder = os.path.join(self.tmp, "t_layers")
        os.makedirs(folder)
        _PIL.new("RGBA", (440, 330), (255, 255, 255, 255)).save(os.path.join(folder, "00_base.png"))
        _PIL.new("RGBA", (200, 50), (0, 0, 0, 255)).save(os.path.join(folder, "01_sale.png"))
        man = {"canvas": [440, 330], "layers": [
            {"z_index": 0, "file": "00_base.png", "box": [0, 0, 440, 330]},
            {"z_index": 1, "file": "01_sale.png", "box": [44, 33, 244, 83], "text": "SALE <50%>",
             "text_lines": [{"runs": [{"text": "SALE <50%>", "style": {"similar_font_family": "Inter",
                                                                      "foreground_color": "#FF0000", "bold": True}}],
                             "bounding_box": {"absolute": [44, 33, 244, 83]}}]}]}
        with open(os.path.join(folder, "layers.json"), "w") as f:
            json.dump(man, f)
        orig = os.path.join(self.tmp, "orig.png")
        _PIL.new("RGB", (400, 300), (255, 255, 255)).save(orig)
        code, out, err = self.run_export("layers", folder, "--original", orig, "--live-text")
        self.assertEqual(code, 0, err)
        self.assertEqual(_PIL.open(os.path.join(folder, "composite.png")).size, (400, 300))
        with open(os.path.join(folder, "layers.svg"), encoding="utf-8") as f:
            svg = f.read()
        self.assertIn(">SALE &lt;50%&gt;</text>", svg)
        self.assertIn('font-family="Inter, sans-serif"', svg)
        self.assertIn('x="40.0"', svg)                     # 44 scaled by 400/440

    def test_split_cuts_items_in_reading_order(self):
        sheet = _PIL.new("RGBA", (900, 600), (0, 0, 0, 0))
        colors = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)]
        spots = [(100, 120), (600, 80), (80, 400), (620, 430)]   # uneven rows on purpose
        for c, (x, y) in zip(colors, spots):
            sheet.paste(c, (x, y, x + 120, y + 100))
        p = os.path.join(self.tmp, "sheet.png")
        sheet.save(p)
        code, out, err = self.run_export("split", p, "--names", "a,b,c,d", "--square")
        self.assertEqual(code, 0, err)
        for name, c in zip("abcd", colors):
            im = _PIL.open(os.path.join(self.tmp, "sheet_parts", name + ".png")).convert("RGBA")
            self.assertEqual(im.width, im.height)
            self.assertEqual(im.getpixel((im.width // 2, im.height // 2)), c)

    def test_split_row_with_mixed_heights(self):
        sheet = _PIL.new("RGBA", (900, 400), (0, 0, 0, 0))
        boxes = [((50, 150, 150, 200), (255, 0, 0, 255)),      # short
                 ((350, 40, 450, 360), (0, 255, 0, 255)),      # tall
                 ((650, 100, 750, 260), (0, 0, 255, 255))]     # medium, centre below the short one
        for b, c in boxes:
            sheet.paste(c, b)
        p = os.path.join(self.tmp, "row.png")
        sheet.save(p)
        code, _, err = self.run_export("split", p, "--names", "a,b,c")
        self.assertEqual(code, 0, err)
        for name, (_, c) in zip("abc", boxes):
            im = _PIL.open(os.path.join(self.tmp, "row_parts", name + ".png")).convert("RGBA")
            self.assertEqual(im.getpixel((im.width // 2, im.height // 2)), c)

    def test_icons_full_set(self):
        src = os.path.join(self.tmp, "logo.png")
        im = _PIL.new("RGBA", (600, 600), (0, 0, 0, 0))
        im.paste((200, 60, 40, 255), (150, 150, 450, 450))
        im.save(src)
        out = os.path.join(self.tmp, "icons")
        code, stdout, err = self.run_export("icons", src, "--out", out, "--bg", "#112233", "--name", "Demo")
        self.assertEqual(code, 0, err)
        for rel, size in (("favicon-32x32.png", 32), ("apple-touch-icon.png", 180), ("icon-512.png", 512),
                          ("icon-maskable-512.png", 512), ("ios/AppIcon.appiconset/AppIcon-1024.png", 1024),
                          ("android/mipmap-xxxhdpi/ic_launcher.png", 192)):
            self.assertEqual(_PIL.open(os.path.join(out, rel)).size, (size, size), rel)
        self.assertEqual(_PIL.open(os.path.join(out, "ios/AppIcon.appiconset/AppIcon-1024.png")).mode, "RGB")
        self.assertEqual(_PIL.open(os.path.join(out, "apple-touch-icon.png")).getpixel((2, 2)), (17, 34, 51))
        self.assertEqual(_PIL.open(os.path.join(out, "favicon-32x32.png")).getpixel((0, 0))[3], 0)
        with open(os.path.join(out, "site.webmanifest"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["name"], "Demo")
        self.assertTrue(os.path.exists(os.path.join(out, "favicon.ico")))
        self.assertIn('rel="manifest"', stdout)

    def test_final_size_exact(self):
        src = os.path.join(self.tmp, "big.png")
        _PIL.new("RGB", (2048, 2048), (10, 20, 30)).save(src)
        fin = seedream.finalize_size(src, "1200x630", "crop")
        self.assertEqual(_PIL.open(fin).size, (1200, 630))
        self.assertTrue(fin.endswith("big_1200x630.png"))

    def test_split_refuses_opaque(self):
        p = os.path.join(self.tmp, "o.png")
        _PIL.new("RGB", (300, 300), (9, 9, 9)).save(p)
        with self.assertRaises(SystemExit):
            self.run_export("split", p)


class SpecTests(unittest.TestCase):
    """SKILL.md must satisfy the agentskills.io frontmatter rules."""

    def test_frontmatter(self):
        with open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8") as f:
            text = f.read()
        m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
        self.assertTrue(m, "missing frontmatter")
        top = dict(re.findall(r"^([a-z-]+):\s*(.*)$", m.group(1), re.M))
        allowed = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
        self.assertLessEqual(set(top), allowed, "non-spec keys: {}".format(set(top) - allowed))
        self.assertRegex(top["name"], r"^[a-z0-9]+(-[a-z0-9]+)*$")
        self.assertEqual(top["name"], os.path.basename(os.path.normpath(SKILL_DIR)))
        self.assertTrue(0 < len(top["description"]) <= 1024, len(top["description"]))
        self.assertLessEqual(len(top["compatibility"]), 500)
        self.assertLess(text.count("\n"), 500, "SKILL.md should stay under 500 lines")

    def test_reference_links_exist(self):
        with open(os.path.join(SKILL_DIR, "SKILL.md"), encoding="utf-8") as f:
            text = f.read()
        for link in re.findall(r"\]\((references/[^)]+)\)", text):
            self.assertTrue(os.path.isfile(os.path.join(SKILL_DIR, link)), link)


if __name__ == "__main__":
    unittest.main()
