"""Panel HTTP yanıtı (I-393, ADR-0167): ETag + 304, gzip, HTTP/1.1 keep-alive, yazma isteğinde bağlantı kapanır."""
import gzip
import http.client
import os
import sys
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import panel  # noqa: E402


class HttpOnbellek(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import http.server
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), panel._isleyici())
        cls.port = cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def _al(self, yol, baslik=None, c=None):
        c = c or http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request("GET", yol, headers=baslik or {})
        r = c.getresponse()
        return c, r, r.read()

    def test_etag_ve_304(self):
        _, r, g = self._al("/app.js")
        self.assertEqual(r.status, 200)
        self.assertEqual(r.getheader("Cache-Control"), "no-cache")
        etag = r.getheader("ETag")
        self.assertTrue(etag)
        _, r2, g2 = self._al("/app.js", {"If-None-Match": etag})
        self.assertEqual((r2.status, g2), (304, b""))

    def test_gzip_kucultur_ve_icerik_ayni(self):
        _, r0, ham = self._al("/app.js")
        _, r, g = self._al("/app.js", {"Accept-Encoding": "gzip"})
        self.assertEqual(r.getheader("Content-Encoding"), "gzip")
        self.assertLess(len(g), len(ham) * 0.5)
        self.assertEqual(gzip.decompress(g), ham)

    def test_gzip_istenmezse_ham(self):
        _, r, g = self._al("/app.js")
        self.assertIsNone(r.getheader("Content-Encoding"))

    def test_keep_alive_tek_baglanti(self):
        c, r1, _ = self._al("/app.css")
        self.assertEqual(r1.version, 11)
        self.assertNotEqual((r1.getheader("Connection") or "").lower(), "close")
        _, r2, _ = self._al("/app.js", c=c)   # aynı bağlantı yeniden kullanılır
        self.assertEqual(r2.status, 200)

    def test_post_baglantiyi_kapatir(self):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        c.request("POST", "/olmayan", body=b"{}", headers={"Content-Type": "application/json", "Content-Length": "2"})
        r = c.getresponse()
        r.read()
        self.assertEqual((r.getheader("Connection") or "").lower(), "close")
        self.assertEqual(r.getheader("Cache-Control"), "no-store")


if __name__ == "__main__":
    unittest.main()
