"""Offline tests: a local mock of the ModelArk API. No network, no real key."""

import base64
import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import seedream  # noqa: E402

FAKE_KEY = "test-key-0123456789abcdef"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


class Mock(BaseHTTPRequestHandler):
    last = {}
    mode = "ok"

    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        Mock.last = {"path": self.path, "auth": self.headers.get("Authorization")}
        self._send(200, {"data": [{"id": "dola-seedream-5-5-261028"}, {"id": "seedance-x"}]})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        Mock.last = {"path": self.path, "auth": self.headers.get("Authorization"),
                     "body": json.loads(self.rfile.read(n))}
        if Mock.mode == "error":
            # A misbehaving server that echoes the auth header back.
            self._send(401, {"error": {"message": "bad token " + self.headers["Authorization"]}})
            return
        self._send(200, {"created": 1, "usage": {"generated_images": 1},
                         "data": [{"b64_json": base64.b64encode(PNG).decode(), "size": "2560x1440"}]})


class SeedreamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = HTTPServer(("127.0.0.1", 0), Mock)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()
        cls.base = "http://127.0.0.1:{}/api/v3".format(cls.srv.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        Mock.mode = "ok"
        os.environ[seedream.ENV_KEY] = FAKE_KEY
        self.tmp = tempfile.mkdtemp()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = seedream.main(["--base-url", self.base] + list(argv))
        return code, out.getvalue(), err.getvalue()

    def all_written_text(self):
        blob = b""
        for root, _, files in os.walk(self.tmp):
            for f in files:
                with open(os.path.join(root, f), "rb") as fh:
                    blob += fh.read()
        return blob

    # --- tests -------------------------------------------------------------

    def test_models_filters_seedream(self):
        code, out, _ = self.run_cli("models")
        self.assertEqual(code, 0)
        self.assertIn("dola-seedream-5-5-261028", out)
        self.assertNotIn("seedance", out)
        self.assertEqual(Mock.last["path"], "/api/v3/models")
        self.assertEqual(Mock.last["auth"], "Bearer " + FAKE_KEY)

    def test_generate_body_files_and_no_key_leak(self):
        ref = os.path.join(self.tmp, "ref.png")
        with open(ref, "wb") as f:
            f.write(PNG)
        out_dir = os.path.join(self.tmp, "out")
        code, out, err = self.run_cli("generate", "--prompt", "A quiet harbour at dawn.",
                                      "--size", "16:9", "--image", ref, "--image", ref,
                                      "--out", out_dir, "--name", "shot")
        self.assertEqual(code, 0, err)
        body = Mock.last["body"]
        self.assertEqual(Mock.last["path"], "/api/v3/images/generations")
        self.assertEqual(body["model"], "dola-seedream-5-5-261028")
        self.assertEqual(body["size"], "2560x1440")
        self.assertEqual(body["response_format"], "b64_json")
        self.assertIs(body["watermark"], False)
        self.assertIsInstance(body["image"], list)
        self.assertTrue(body["image"][0].startswith("data:image/png;base64,"))

        png = os.path.join(out_dir, "shot.png")
        txt = os.path.join(out_dir, "shot.txt")
        with open(png, "rb") as f:
            self.assertEqual(f.read(), PNG)
        with open(txt, encoding="utf-8") as f:
            side = f.read()
        self.assertIn("A quiet harbour at dawn.", side)
        self.assertIn("2560x1440", side)
        self.assertIn("sha256", side)
        self.assertNotIn("base64,", side)  # image bytes not dumped into the sidecar

        self.assertNotIn(FAKE_KEY, out + err)
        self.assertNotIn(FAKE_KEY.encode(), self.all_written_text())

    def test_single_image_is_string_and_no_overwrite(self):
        ref = os.path.join(self.tmp, "ref.png")
        with open(ref, "wb") as f:
            f.write(PNG)
        out_dir = os.path.join(self.tmp, "out")
        for _ in range(2):
            code, _, err = self.run_cli("generate", "--prompt", "x", "--image", ref,
                                        "--out", out_dir, "--name", "a")
            self.assertEqual(code, 0, err)
        self.assertIsInstance(Mock.last["body"]["image"], str)
        self.assertTrue(os.path.exists(os.path.join(out_dir, "a.png")))
        self.assertTrue(os.path.exists(os.path.join(out_dir, "a_2.png")))
        self.assertTrue(os.path.exists(os.path.join(out_dir, "a_2.txt")))

    def test_error_text_is_scrubbed(self):
        Mock.mode = "error"
        code, out, err = self.run_cli("generate", "--prompt", "x", "--out", self.tmp)
        self.assertEqual(code, 1)
        self.assertIn("HTTP 401", err)
        self.assertNotIn(FAKE_KEY, out + err)

    def test_size_validation(self):
        self.assertEqual(seedream.parse_size("2:3"), "1728x2592")
        self.assertEqual(seedream.parse_size("1:1"), "2048x2048")
        self.assertEqual(seedream.parse_size("1280x720"), "1280x720")  # exactly 921,600
        with self.assertRaises(seedream.HelperError):
            seedream.parse_size("1024x768")

    def test_missing_key(self):
        del os.environ[seedream.ENV_KEY]
        code, _, err = self.run_cli("generate", "--prompt", "x", "--out", self.tmp)
        self.assertEqual(code, 1)
        self.assertIn("ARK_API_KEY is not set", err)

    def test_dry_run_needs_no_key(self):
        del os.environ[seedream.ENV_KEY]
        code, out, _ = self.run_cli("generate", "--prompt", "x", "--size", "1:1", "--dry-run")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["size"], "2048x2048")

    def test_extra_cannot_override_reserved(self):
        code, _, err = self.run_cli("generate", "--prompt", "x", "--dry-run",
                                    "--extra", '{"prompt": "y"}')
        self.assertEqual(code, 1)
        self.assertIn("own flag", err)


if __name__ == "__main__":
    unittest.main()
