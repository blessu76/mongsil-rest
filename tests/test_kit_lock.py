"""scripts/kit_lock.py — lock 일치·불일치·킷 없음을 임시 폴더에서 검증한다(실제 vendor/ 는 건드리지 않는다)."""
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import kit_lock  # noqa: E402

VENDOR_PY = (
    "import sys\n"
    "sys.exit(0 if len(sys.argv) > 2 and sys.argv[1] == 'verify' else 2)\n"
)


def make_root(tmp, *, install=True, tag="v1.0.0", commit="abc123", stamp=None, manifest=b"files\n", lock_manifest=None):
    root = Path(tmp)
    (root / "vendor").mkdir()
    msha = lock_manifest or hashlib.sha256(manifest).hexdigest()
    (root / kit_lock.LOCK).write_text(
        "# test lock\ntag=%s\ncommit=%s\nmanifest_sha256=%s\n" % (tag, commit, msha), encoding="utf-8")
    if install:
        pkg = root / kit_lock.PKG
        pkg.mkdir()
        (pkg / "KIT_VERSION").write_text(stamp or "%s %s\n" % (tag, commit), encoding="utf-8")
        (pkg / "MANIFEST.sha256").write_bytes(manifest)
        (pkg / "vendor.py").write_text(VENDOR_PY, encoding="utf-8")
    return root


class KitLockTest(unittest.TestCase):
    def test_matching_lock_has_no_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(kit_lock.problems(make_root(tmp)), [])
            self.assertEqual(kit_lock.main(["--root", tmp, "check"]), 0)

    def test_version_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp, stamp="v0.9.0 deadbeef\n")
            bad = kit_lock.problems(root)
            self.assertTrue(any("differs from the lock" in b for b in bad), bad)
            self.assertEqual(kit_lock.main(["--root", tmp, "check"]), 1)

    def test_manifest_hash_mismatch_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp, lock_manifest="0" * 64)
            bad = kit_lock.problems(root)
            self.assertTrue(any("manifest hash" in b for b in bad), bad)
            self.assertEqual(kit_lock.main(["--root", tmp, "check"]), 1)

    def test_missing_kit_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp, install=False)
            self.assertEqual(kit_lock.problems(root), ["%s is not installed" % kit_lock.PKG])
            self.assertEqual(kit_lock.main(["--root", tmp, "check"]), 1)

    def test_missing_vendor_py_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_root(tmp)
            (root / kit_lock.PKG / "vendor.py").unlink()
            self.assertTrue(any("vendor.py missing" in b for b in kit_lock.problems(root)))

    def test_missing_or_incomplete_lock_exits(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                kit_lock.read_lock(tmp)
            (Path(tmp) / "vendor").mkdir()
            (Path(tmp) / kit_lock.LOCK).write_text("tag=v1\n", encoding="utf-8")
            with self.assertRaises(SystemExit) as cm:
                kit_lock.read_lock(tmp)
            self.assertIn("missing commit", str(cm.exception))

    def test_sync_rejects_a_non_kit_folder(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as notkit:
            root = make_root(tmp, install=False)
            with self.assertRaises(SystemExit) as cm:
                kit_lock.sync(root, notkit)
            self.assertIn("not an ipe_web_kit clone", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
