import importlib.util
import os
import platform
import shutil
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTDATA_DIR = PROJECT_ROOT / "testdata"
TEST_M4A = TESTDATA_DIR / "test.m4a"


def _find_module():
    env = os.environ.get("MP4GAINPY_PYTHON_MODULE")
    if env:
        return Path(env)

    system = platform.system()
    if system == "Linux":
        extensions = [".so"]
        prefixes = ["libmp4gainpy", "mp4gainpy"]
    elif system == "Darwin":
        extensions = [".dylib", ".so"]
        prefixes = ["libmp4gainpy", "mp4gainpy"]
    elif system == "Windows":
        extensions = [".pyd", ".dll"]
        prefixes = ["mp4gainpy"]
    else:
        extensions = [".so"]
        prefixes = ["libmp4gainpy", "mp4gainpy"]

    for build_type in ["debug", "release"]:
        for prefix in prefixes:
            for ext in extensions:
                candidate = PROJECT_ROOT / "target" / build_type / f"{prefix}{ext}"
                if candidate.exists():
                    return candidate

    return None


def _load_module():
    # Prefer whatever's already installed in the active Python env (e.g. via
    # `maturin develop`). Fall back to loading the raw cdylib from target/.
    try:
        import mp4gainpy  # type: ignore[import-not-found]

        return mp4gainpy
    except ImportError:
        pass

    path = _find_module()
    if path is None:
        raise RuntimeError(
            "Could not find mp4gainpy module. "
            "Run `uv run maturin develop --features python` first, "
            "or set MP4GAINPY_PYTHON_MODULE to the shared library path."
        )
    spec = importlib.util.spec_from_file_location("mp4gainpy", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mp4gainpy = _load_module()


class Mp4GainPyTest(unittest.TestCase):
    def test_gain_step_db_constant(self):
        self.assertEqual(mp4gainpy.GAIN_STEP_DB, 1.5)

    # -- bytes API --

    def test_bytes_zero_is_noop(self):
        data = TEST_M4A.read_bytes()
        self.assertEqual(mp4gainpy.aac_apply_gain(data, 0), data)

    def test_bytes_preserves_length(self):
        data = TEST_M4A.read_bytes()
        out = mp4gainpy.aac_apply_gain(data, 2)
        self.assertEqual(len(out), len(data))

    def test_bytes_positive_mutates(self):
        data = TEST_M4A.read_bytes()
        out = mp4gainpy.aac_apply_gain(data, 2)
        self.assertNotEqual(out, data)

    def test_bytes_negative_mutates(self):
        data = TEST_M4A.read_bytes()
        out = mp4gainpy.aac_apply_gain(data, -2)
        self.assertNotEqual(out, data)

    def test_bytes_inverse_round_trip(self):
        data = TEST_M4A.read_bytes()
        up = mp4gainpy.aac_apply_gain(data, 2)
        back = mp4gainpy.aac_apply_gain(up, -2)
        self.assertEqual(back, data)

    def test_bytes_not_m4a_raises(self):
        with self.assertRaises(RuntimeError):
            mp4gainpy.aac_apply_gain(b"\x00" * 128, 2)

    def test_bytes_returns_bytes_type(self):
        data = TEST_M4A.read_bytes()
        self.assertIsInstance(mp4gainpy.aac_apply_gain(data, 2), bytes)

    # -- file API --

    def test_file_zero_is_noop(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir) / "test.m4a"
            shutil.copy2(TEST_M4A, tmp)
            before = tmp.read_bytes()
            self.assertEqual(mp4gainpy.aac_apply_gain_file(str(tmp), 0), 0)
            self.assertEqual(tmp.read_bytes(), before)

    def test_file_positive_mutates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir) / "test.m4a"
            shutil.copy2(TEST_M4A, tmp)
            before = tmp.read_bytes()
            modified = mp4gainpy.aac_apply_gain_file(str(tmp), 2)
            self.assertGreater(modified, 0)
            self.assertNotEqual(tmp.read_bytes(), before)

    def test_file_nonexistent_raises(self):
        with self.assertRaises(RuntimeError):
            mp4gainpy.aac_apply_gain_file("/nonexistent/path/file.m4a", 2)

    def test_file_non_m4a_raises(self):
        with self.assertRaises(RuntimeError):
            mp4gainpy.aac_apply_gain_file(str(PROJECT_ROOT / ".gitignore"), 2)


if __name__ == "__main__":
    unittest.main()
