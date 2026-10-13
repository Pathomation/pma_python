"""Tests for _collect_slide_package_files: multi-file slides must be uploaded with their image data."""
import asyncio
import os
import shutil
import tempfile
import unittest
from unittest import mock

from pma_python import core

REAL_PMA_START_HELPER = core._pma_start_files_for_slide


def write(path, size):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"x" * size)
    return path


class CollectSlidePackageFiles(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        # by default PMA.start is not running
        p = mock.patch.object(core, "_pma_start_files_for_slide", return_value=[])
        p.start()
        self.addCleanup(p.stop)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def rel(self, files):
        return [f["relative_path"] for f in files]

    def test_olympus_vsi_underscore_folder(self):
        vsi = write(os.path.join(self.dir, "VL1_Name, A_1AH&E.vsi"), 100)
        write(os.path.join(self.dir, "_VL1_Name, A_1AH&E_", "stack1", "frame_t.ets"), 5000)
        write(os.path.join(self.dir, "_VL1_Name, A_1AH&E_", "stack10001", "frame_t.ets"), 300)
        files = core._collect_slide_package_files(vsi)
        self.assertEqual(self.rel(files), [
            "VL1_Name, A_1AH&E.vsi",
            "_VL1_Name, A_1AH&E_/stack1/frame_t.ets",
            "_VL1_Name, A_1AH&E_/stack10001/frame_t.ets",
        ])
        self.assertTrue(files[0]["is_main"])
        self.assertFalse(any(f["is_main"] for f in files[1:]))
        self.assertEqual(core._get_slide_package_size(vsi), (5400, 5000))

    def test_mrxs_same_name_folder(self):
        mrxs = write(os.path.join(self.dir, "slide.mrxs"), 10)
        write(os.path.join(self.dir, "slide", "Data0000.dat"), 700)
        write(os.path.join(self.dir, "slide", "Slidedat.ini"), 20)
        self.assertEqual(self.rel(core._collect_slide_package_files(mrxs)),
                         ["slide.mrxs", "slide/Data0000.dat", "slide/Slidedat.ini"])

    def test_single_file_slide(self):
        svs = write(os.path.join(self.dir, "single.svs"), 42)
        write(os.path.join(self.dir, "other.svs"), 42)          # unrelated neighbour
        files = core._collect_slide_package_files(svs)
        self.assertEqual(self.rel(files), ["single.svs"])
        self.assertEqual(core._get_slide_package_size(svs), (42, 42))

    def test_pma_start_list_is_merged_without_duplicates(self):
        vsi = write(os.path.join(self.dir, "a.vsi"), 1)
        ets = write(os.path.join(self.dir, "_a_", "stack1", "frame_t.ets"), 9)
        extra = write(os.path.join(self.dir, "a_extra", "x.bin"), 3)   # a convention we do not know
        outside = write(os.path.join(tempfile.mkdtemp(), "elsewhere.bin"), 3)
        with mock.patch.object(core, "_pma_start_files_for_slide", return_value=[vsi, ets, extra, outside]):
            files = core._collect_slide_package_files(vsi)
        self.assertEqual(self.rel(files), ["a.vsi", "_a_/stack1/frame_t.ets", "a_extra/x.bin"])
        shutil.rmtree(os.path.dirname(outside), ignore_errors=True)

    def test_pma_start_unavailable_is_not_fatal(self):
        vsi = write(os.path.join(self.dir, "b.vsi"), 1)
        write(os.path.join(self.dir, "_b_", "stack1", "frame_t.ets"), 9)
        with mock.patch.object(core, "get_files_for_slide", side_effect=ConnectionError("PMA.start down")), \
             mock.patch.object(core, "_pma_start_files_for_slide", side_effect=REAL_PMA_START_HELPER):
            files = core._collect_slide_package_files(vsi)
        self.assertEqual(self.rel(files), ["b.vsi", "_b_/stack1/frame_t.ets"])

    def test_missing_file(self):
        with self.assertRaises(ValueError):
            core._collect_slide_package_files(os.path.join(self.dir, "nope.vsi"))


class RealPmaStartHelper(unittest.TestCase):
    def test_returns_empty_list_when_pma_start_errors(self):
        with mock.patch.object(core, "get_files_for_slide", side_effect=ConnectionError("down")):
            self.assertEqual(core._pma_start_files_for_slide("C:/x.vsi"), [])

    def test_returns_paths_from_pma_start(self):
        with mock.patch.object(core, "get_files_for_slide", return_value={"C:/x.vsi": {}, "C:/_x_/s/f.ets": {}}):
            self.assertEqual(sorted(core._pma_start_files_for_slide("C:/x.vsi")), ["C:/_x_/s/f.ets", "C:/x.vsi"])


class CloudUploadSendsWholeSlide(unittest.TestCase):
    """End to end through upload_file_on_cloud with a fake server: every file must be announced and sent."""

    def test_vsi_upload_sends_image_data(self):
        d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, d, True)
        vsi = write(os.path.join(d, "VL9_X, Y_1AH&E.vsi"), 100)
        write(os.path.join(d, "_VL9_X, Y_1AH&E_", "stack1", "frame_t.ets"), 5000)

        sent = []

        class FakeResp:
            id, upload_type, urls, multipart_files = 7, 2, ["u1", "u2"], []

        class FakeClient:
            server_url = "https://pma.example/"

            def __init__(self, url):
                pass

            async def upload_header(self, header, session_id):
                self.header = header
                sent.append(("header", [(f.path, f.length, f.isMain) for f in header.files]))
                return FakeResp()

            async def upload_file(self, upload_id, upload_type, url, rel, stream, session_id, **kw):
                sent.append(("file", rel, len(stream.read())))

        class Ok:
            status_code = 200

        with mock.patch.object(core, "PmaCoreClient", FakeClient), \
             mock.patch.object(core, "_pma_start_files_for_slide", return_value=[]), \
             mock.patch.object(core.requests, "get", return_value=Ok()), \
             mock.patch.object(core, "get_slide_info", return_value={}):
            ok, err = asyncio.run(core.upload_file_on_cloud(
                pma_core_url="https://pma.example/", session_id="S", slide_path=vsi,
                upload_directory="Slides/Received"))

        self.assertTrue(ok, err)
        self.assertEqual(sent[0], ("header", [("VL9_X, Y_1AH&E.vsi", 100, True),
                                              ("_VL9_X, Y_1AH&E_/stack1/frame_t.ets", 5000, False)]))
        self.assertEqual(sent[1:], [("file", "VL9_X, Y_1AH&E.vsi", 100),
                                    ("file", "_VL9_X, Y_1AH&E_/stack1/frame_t.ets", 5000)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
