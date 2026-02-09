import asyncio
import unittest
import tempfile
import os
from PIL import Image
from pma_python import core

class CoreTest(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.core307 = "https://dev.pathomation.com/core_dev"
        self.core301 = "https://snapshot.pathomation.com/PMA.core/3.0.1/"
        self.local_folder = "C:\\slides"
        self.username = "pma_admin"
        self.password = "P4th0-M4t!on"
        self.local_file1 = "C:\\slides\\APPS115_11139_rescan_01.btf"
        self.local_file2 = "C:/Slides/14.svs"
        self.local_file3 = "C:/Slides/CMU-1.mrxs"
        self.core_file1 = "_sys_aws_s3/A_download/part.tif"
        self.core_file2 = "_sys_aws_s3/brightfield/Test_slide_pathomation_admin.svs"
        self.core_file3 = "_sys_aws_s3/2DollarBill.zif"
        self.core_zarr_file = "_sys_aws_s3/brightfield/OMERO/H2018-1180exp1s2HP-114785-20191111_zarr/METADATA.ome.xml"
        self._pma_pmacoreliteURL = "http://localhost:54001/"
        self.first_n_em_dir = "_sys_aws_s3/annotations"
        self.label_url = "https://snapshot.pathomation.com/PMA.core/3.0.3/barcode?SessionID=NjpybCWmdMJfCTRNdqa7PA2&pathOrUid=_sys_aws_s3%2Falignment%2Fcasus001%2Fcasus001_HE_1.mrxs&w=300&h=150"
        self.barcode_text = ['UZBrussel23B6793-A-1-1HE']
        self.thumbnail_url = "https://snapshot.pathomation.com/PMA.core/3.0.3/thumbnail?SessionID=NjpybCWmdMJfCTRNdqa7PA2&pathOrUid=_sys_aws_s3%2Falignment%2Fcasus001%2Fcasus001_HE_1.mrxs&w=150&h=150"
        self.macro_url = 'https://snapshot.pathomation.com/PMA.core/3.0.3/macro?SessionID=NjpybCWmdMJfCTRNdqa7PA2&pathOrUid=_sys_aws_s3%2Falignment%2Fcasus001%2Fcasus001_HE_1.mrxs&w=200&h=200'
        self.tile_url = 'https://snapshot.pathomation.com/PMA.core/3.0.3/tile?sessionID=NjpybCWmdMJfCTRNdqa7PA2&channels=0&timeframe=0&layer=0&pathOrUid=_sys_aws_s3%2Falignment%2Fcasus001%2Fcasus001_HE_1.mrxs&x=10&y=20&z=2&format=png&quality=90&cache=true'
        self.tmp_upload_dir = "_sys_aws_s3/alignment/moving"
        self.tmp_download_dir = "C:\\Users\\VitalijVictorPathoma\\Downloads"
        self.session_id = core.connect(self.core307, self.username, self.password)

    def test_check_session_id(self):
        session_id = core.connect(self.core307, self.username, self.password)
        print(session_id)
        self.assertIsNotNone(session_id)

    def test_set_debug_flag(self):
        flag = core.set_debug_flag(flag=False)
        print(flag)
        self.assertIsNone(flag)

    def test_pma_session_id(self):
        session_id = core._pma_session_id()
        self.assertEqual(session_id, core.connect(self.core307, self.username, self.password))
        print(session_id)

    def test_pma_first_session_id(self):
        first_session_id = core._pma_first_session_id()
        print(first_session_id)
        self.assertIsNotNone(first_session_id)

    def test_pma_url(self):
        pma_url = core._pma_url()
        print(pma_url)
        self.assertEqual(pma_url, self.core307)

    def test_pma_api_url(self):
        api_url = core._pma_api_url()
        print(api_url)
        self.assertEqual(api_url, self.core307 + "api/json/")

    def test__pma_query_url(self):
        query_url = core._pma_query_url()
        print(query_url)
        self.assertEqual(query_url, self.core307 + "query/json/")

    def test_pma_is_lite(self):
        lite_URL_bool = core._pma_is_lite(self._pma_pmacoreliteURL)
        print(lite_URL_bool)
        self.assertTrue(True)

    def test_get_version_info(self):
        version = core.get_version_info(self.core307)
        print(version)
        self.assertIsNotNone(version)

    def test_get_build_revision(self):
        revision = core.get_build_revision(self.core307, verify=True)
        print(revision)
        self.assertIsNotNone(revision)
        self.assertIn("1f204cca", revision)

    def test_get_api_version(self):
        api_version = core.get_api_version(pmacoreURL=self.core307, verify=False)
        print(api_version)
        self.assertIsNotNone(api_version)
        if isinstance(api_version, dict):
            self.assertEquals("[3, 0, 2]", api_version)

    def test_get_api_verion_string(self):
        api_version_string = core.get_api_verion_string(pmacoreURL=self.core307)
        print(api_version_string)
        self.assertIsNotNone(api_version_string)
        self.assertTrue(len(api_version_string) > 0)
        self.assertRegex(api_version_string, r"^\d+(\.\d+)*$")

    def test_register_session_id(self):
        core.register_session_id(self.session_id, self.core307)
        self.assertIn(self.session_id, core._pma_sessions)
        self.assertEqual(core._pma_sessions[self.session_id], self.core307)
        self.assertIn(self.session_id, core._pma_amount_of_data_downloaded)
        self.assertEqual(core._pma_amount_of_data_downloaded[self.session_id], 0)
        self.assertIn(self.session_id, core._pma_slideinfos)
        self.assertEqual(core._pma_slideinfos[self.session_id], {})

    def test_connect(self):
        self.assertIsNotNone(self.session_id)
        self.assertIn(self.session_id, core._pma_sessions)
        self.assertEqual(core._pma_sessions[self.session_id], self.core307)
        self.assertIn(self.session_id, core._pma_usernames)
        self.assertEqual(core._pma_usernames[self.session_id], self.username)
        self.assertIn(self.session_id, core._pma_slideinfos)
        self.assertEqual(core._pma_slideinfos[self.session_id], {})
        self.assertIn(self.session_id, core._pma_amount_of_data_downloaded)

    def test_get_root_directories(self):
        directories = core.get_root_directories(self.session_id)
        print(directories)
        self.assertGreater(len(directories), 0)

    def test_pma_merge_dict_values(self):
        input_dict = {
            "key1": [1, 2, 3],
            "key2": [3, 4, 5],
            "key3": [5, 6, 7],
        }
        expected_result = ["1", "2", "3", "4", "5", "6", "7"]
        result = core._pma_merge_dict_values(input_dict)
        self.assertEqual(result, expected_result)

    def test_get_directories(self):
        root_directories = core.get_root_directories(self.session_id, False)
        first_directory = root_directories[0]
        directories = core.get_directories(first_directory, self.session_id)
        print(directories)
        self.assertIsInstance(directories, list)

    def test_get_first_non_empty_directory(self):
        f_non_em_dir = core.get_first_non_empty_directory(self.first_n_em_dir, self.session_id)
        print(f_non_em_dir)
        self.assertIsNotNone(f_non_em_dir)

    def test_get_slides(self):
        root_directories = core.get_root_directories(core.connect(self.core307, self.username, self.password))
        first_directory = root_directories[0]
        slides = core.get_slides(first_directory, self.session_id)
        print(slides)
        self.assertIsInstance(slides, list)

    def test_get_slide_info(self):
        slide_info = core.get_slide_info(self.core_file1, self.session_id)
        print(slide_info)
        self.assertIn("PhysicalSize", slide_info)

    def test_get_slide_file_extension(self):
        ext = core.get_slide_file_extension(self.core_file1)
        print(ext)
        self.assertEqual(ext, ".mrxs")

    def test_get_slide_file_name(self):
        name = core.get_slide_file_name(self.core_file1)
        print(name)
        self.assertEqual(name, "casus001_HE_1.mrxs")

    def test_get_uid(self):
        uid = core.get_uid(self.core_file1, self.session_id)
        print(uid)
        self.assertEqual(uid, "HI6XH9DOFL")

    def test_get_fingerprint(self):
        fingerprint = core.get_fingerprint(self.core_file1, self.session_id)
        print(fingerprint)
        self.assertEqual(fingerprint, "E2pG0KLJbrKSBGwXmpqtVYPRErY1")

    def test_who_am_i(self):
        result = core.who_am_i(self.session_id)
        print(result)
        self.assertEqual(result, {
        "sessionID": self.session_id,
        "username": "vitalij",
        "url": self.core307,
        "amountOfDataDownloaded": 8
    })

    def test_sessions(self):
        sessions = core.sessions()
        print(sessions)
        self.assertIsInstance(sessions, dict)
        self.assertIn(self.session_id, sessions)

    def test_get_max_zoomlevel(self):
        result = core.get_max_zoomlevel(self.core_file1, self.session_id)
        print(result)
        self.assertEqual(result, 9)

    def test_get_pixels_per_micrometer(self):
        result = core.get_pixels_per_micrometer(self.core_file1, self.session_id, zoomlevel=2)
        print(result)
        self.assertEqual(result, (35.04761904761907, 35.04761904761907))

    def test_get_number_of_tiles(self):
        result = core.get_number_of_tiles(self.core_file1, 2, self.session_id)
        print(result)
        self.assertEqual(result, (132, 366, 48312))

    def test_get_physical_dimensions(self):
        result = core.get_physical_dimensions(self.core_file1, sessionID=self.session_id)
        print(result)
        self.assertEqual(result, (22954.0, 16413.607))

    def test_get_number_of_channels(self):
        result = core.get_number_of_channels(self.core_file1, sessionID=self.session_id)
        print(result)
        self.assertEqual(result, 1)

    def test_get_number_of_layers(self):
        result = core.get_number_of_layers(self.core_file1, sessionID=self.session_id)
        print(result)
        self.assertEqual(result, 1)

    def test_get_number_of_z_stack_layers(self):
        result = core.get_number_of_z_stack_layers(self.core_file1, sessionID=self.session_id)
        print(result)
        self.assertEqual(result, 1)

    def test_is_fluorescent(self):
        result = core.is_fluorescent(self.core_file1, sessionID=self.session_id)
        print(result)
        self.assertFalse(result)

    def test_is_multi_layer(self):
        result = core.is_multi_layer(self.core_file1, sessionID=self.session_id)
        print(result)
        self.assertFalse(result)

    def test_is_z_stack(self):
        result = core.is_z_stack(self.core_file1, sessionID=self.session_id)
        print(result)
        self.assertFalse(result)

    def test_get_barcode_url(self):
        result = core.get_barcode_url(self.core_file1, width=200, height=100, sessionID=self.session_id)
        print(result)
        self.assertEqual(result,
                         "https://snapshot.pathomation.com/PMA.core/3.0.3/barcode?SessionID=NjpybCWmdMJfCTRNdqa7PA2&pathOrUid=_sys_aws_s3%2Falignment%2Fcasus001%2Fcasus001_HE_1.mrxs&w=200&h=100")

    def test_get_barcode_image(self):
        result = core.get_barcode_image(self.core_file1, width=200, height=100, sessionID=self.session_id)
        print(result)
        self.assertIsInstance(result, Image.Image)

    def test_get_barcode_text(self):
        result = core.get_barcode_text('_sys_aws_s3/client_slides/ASI/DICOM from Michal/10x_BF_01_0.dcm', sessionID=self.session_id)
        print(result)
        self.assertEqual(result, self.barcode_text)

    def test_get_label_url(self):
        result = core.get_label_url(self.core_file1, width=300, height=150, sessionID=self.session_id)
        print(result)
        self.assertEqual(result,
                         self.label_url)

    def test_get_label_image(self):
        result = core.get_label_image(self.core_file1, width=300, height=150, sessionID=self.session_id)
        print(result)
        self.assertIsInstance(result, Image.Image)

    def test_get_thumbnail_url(self):
        result = core.get_thumbnail_url(self.core_file1, width=150, height=150, sessionID=self.session_id)
        print(result)
        self.assertEqual(result, self.thumbnail_url)

    def test_get_thumbnail_image(self):
        result = core.get_thumbnail_image(self.core_file1, width=150, height=150, sessionID=self.session_id)
        print(result)
        self.assertIsInstance(result, Image.Image)

    def test_get_macro_url(self):
        result = core.get_macro_url(self.core_file1, width=200, height=200, sessionID=self.session_id)
        print(result)
        self.assertEqual(result, self.macro_url)

    def test_get_macro_image(self):
        result = core.get_macro_image(self.core_file1, width=200, height=200, sessionID=self.session_id)
        print(result)
        self.assertIsInstance(result, Image.Image)

    def test_get_tile_url(self):
        result = core.get_tile_url(self.core_zarr_file, x=10000, y=100020, zoomlevel=2, zstack=0, sessionID=self.session_id,
                                   format="png", quality=90)
        print(result)
        self.assertEqual(result, self.tile_url)

    def test_get_tile(self):
        result = core.get_tile(self.core_zarr_file, x=10, y=20, zoomlevel=2, zstack=0, sessionID=self.session_id,
                               format="png", quality=100)
        print(result)
        self.assertIsInstance(result, Image.Image)

    def test_get_region(self):
        result = core.get_region(
            self.core_zarr_file,
            x=50,
            y=50,
            width=100,
            height=100,
            scale=1,
            zstack=0,
            sessionID=self.session_id,
            format="png",
            quality=80
        )
        print(result)
        self.assertIsInstance(result, Image.Image)

    def test_get_available_forms(self):
        result = core.get_available_forms(self.core_file1, sessionID=self.session_id)
        print(result)
        self.assertIsInstance(result, dict)

    def test_get_physical_dimensions(self):
        dimensions = core.get_physical_dimensions(self.core_file2, self.session_id)
        print(dimensions)
        self.assertIsNotNone(dimensions)

    def test_get_pixel_dimensions(self):
        dimensions = core.get_pixel_dimensions(self.core_file1, self.session_id)
        print(dimensions)
        self.assertIsNotNone(dimensions)

    def test_get_number_of_tiles(self):
        tiles = core.get_number_of_tiles(self.core_file1, self.session_id)
        print(f"Tiles: {tiles}")
        self.assertGreater(tiles[0], 0, "The number of tiles should be greater than 0.")

    def test_prepare_form_dictionary(self):
        result = core.prepare_form_dictionary("test_form", sessionID=self.session_id)
        print(result)
        self.assertIsInstance(result, dict)

    def test_submit_form_data(self):
        result = core.submit_form_data(self.core_file1, "test_form", {"Field1": "Value1"}, sessionID=self.session_id)
        print(result)
        self.assertIsNone(result)

    def test_get_annotations(self):
        result = core.get_annotations(self.core_file1, sessionID=self.session_id)
        print(result)
        self.assertIsInstance(result, list)

    def test_get_tiles(self):
        tiles = list(
            core.get_tiles(self.core_zarr_file, fromX=0, fromY=0, toX=2, toY=2, zoomlevel=1, sessionID=self.session_id))
        print(tiles)
        self.assertEqual(len(tiles), 4)
        self.assertIsInstance(tiles[0], Image.Image)

    def test_show_slide(self):
        # This test might not work in automated environments since it launches a browser.
        try:
            core.show_slide(self.core_file1, sessionID=self.session_id)
        except Exception as e:
            self.fail(f"Unexpected exception: {e}")

    def test_get_files_for_slide(self):
        result = core.get_files_for_slide(self.core_file1, sessionID=self.session_id)
        print(result)
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_search_slides(self):
        result = core.search_slides(self.first_n_em_dir, "*.mrxs", sessionID=self.session_id)
        print(result)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_pma_upload_callback(self):
        monitor = type("Monitor", (), {"bytes_read": 500, "len": 1000, "previous": None})()
        core._pma_upload_callback(monitor, "test_file")
        self.assertEqual(monitor.previous, 0.5)

    def test_pma_upload_amazon_callback(self):
        result = core._pma_upload_amazon_callback(500, 1000, None, "test_file")
        self.assertEqual(result, 0.5)

    def test_upload(self):
        try:
            core.upload(self.local_file1, self.tmp_upload_dir, self.session_id, True)
            print("Upload completed successfully.")
        except Exception as e:
            self.fail(f"Upload failed: {e}")

    def test_download(self):
        try:
            core.download(self.core_file1, self.local_folder, core.connect(self.core307, self.username, self.password))
            print("Download completed successfully.")
        except Exception as e:
            self.fail(f"Download failed: {e}")

    def test_dummy_annotation(self):
        result = core.dummy_annotation()
        print(result)
        self.assertIsInstance(result, dict)
        self.assertIn("classification", result)
        self.assertIn("notes", result)
        self.assertIn("geometry", result)
        self.assertIn("color", result)
        self.assertIn("fillColor", result)
        self.assertIn("lineThickness", result)
        self.assertEqual(result["color"], "#000000")
        self.assertEqual(result["fillColor"], "#FFFFFF00")
        self.assertEqual(result["lineThickness"], 1)

    def test_add_annotation(self):
        result = core.add_annotation(
            slideRef=self.core_file1,
            classification="tumor",
            notes="Test annotation",
            ann="POINT(16811.622573760804 10669.426317478705)",
            color="#FF0000",
            layerID=1,
            sessionID=self.session_id
        )
        print(result)
        self.assertEqual(result["Code"], "Success")

    def test_add_annotations(self):
        annotations = [
            {
                "geometry": "POINT(16811.622573760804 10669.426317478705)",
                "color": "#FF0000",
                "fillColor": "#FFAAAA",
                "lineThickness": 2,
                "Notes": "Test1 annotation"
            },
            {
                "geometry": "POLYGON((25918 11054,27264 12016,27842 12594,28804 13426,29188 13748,29380 13812,29702 13812,30150 13492,30600 13170,31112 12530,31496 12208,31562 11952,31690 11888,31562 11696,31432 11568,31368 11438,31176 11310,31048 11054,25918 11054))",
                "color": "#00FF00",
                "fillColor": "#AAFFAA",
                "lineThickness": 3,
                "Notes": "Test2 annotation"
            }
        ]

        result = core.add_annotations(
            slideRef=self.core_file1,
            classification="tumor",
            notes="",
            anns=annotations,
            color="#000000",
            layerID=1,
            sessionID=self.session_id
        )
        print(result)
        self.assertEqual(result["Code"], "Success")

    def test_clear_all_annotations(self):
        result = core.clear_all_annotations(slideRef=self.core_file1, sessionID=self.session_id)
        print(result)
        self.assertTrue(result)

    def test_clear_annotations(self):
        result = core.clear_annotations(slideRef=self.core_file1, layerID=1, sessionID=self.session_id)
        print(result)
        self.assertTrue(result)

    def test_get_annotation_surface_area(self):
        result = core.get_annotation_surface_area(
            slideRef=self.core_file1,
            layerID=1,
            annotationID="???????",
            sessionID=self.session_id
        )
        print(result)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_get_annotation_distance(self):
        result = core.get_annotation_distance(
            slideRef=self.core_file1,
            layerID=1,
            annotationID="??????",
            sessionID=self.session_id
        )
        print(result)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    # =========================
    # COMMON SETUP
    # =========================

    async def asyncSetUp(self):
        # create fake slide file
        fd, path = tempfile.mkstemp(suffix=".mrxs")
        os.write(fd, b"fake data")
        os.close(fd)

        self.fake_slide_path = path

        self.valid_params = {
            "pma_core_url": "https://snapshot.pathomation.com/PMA.core_QC",
            "session_id": "valid_session_id",
            "slide_path": self.fake_slide_path,
            "upload_directory": "Amazon_S3/A_download",
            "progress_callback": None,
        }

    async def asyncTearDown(self):
        if os.path.exists(self.fake_slide_path):
            os.remove(self.fake_slide_path)

    # =========================
    # VALIDATION TESTS
    # =========================

    async def test_empty_pma_core_url(self):
        params = dict(self.valid_params)
        params["pma_core_url"] = ""

        ok, reason = await core.large_files_upload_package(**params)

        self.assertFalse(ok)
        self.assertIn("pma_core_url", reason)

    async def test_pma_core_url_not_string(self):
        params = dict(self.valid_params)
        params["pma_core_url"] = 123

        ok, reason = await core.large_files_upload_package(**params)

        self.assertFalse(ok)
        self.assertIn("pma_core_url", reason)

    async def test_empty_session_id(self):
        params = dict(self.valid_params)
        params["session_id"] = ""

        ok, reason = await core.large_files_upload_package(**params)

        self.assertFalse(ok)
        self.assertIn("session_id", reason)

    async def test_session_id_not_string(self):
        params = dict(self.valid_params)
        params["session_id"] = None

        ok, reason = await core.large_files_upload_package(**params)

        self.assertFalse(ok)
        self.assertIn("session_id", reason)

    async def test_empty_slide_path(self):
        params = dict(self.valid_params)
        params["slide_path"] = ""

        ok, reason = await core.large_files_upload_package(**params)

        self.assertFalse(ok)
        self.assertIn("slide_path", reason)

    async def test_slide_path_not_exists(self):
        params = dict(self.valid_params)
        params["slide_path"] = "C:/this/path/does/not/exist.mrxs"

        ok, reason = await core.large_files_upload_package(**params)

        self.assertFalse(ok)
        self.assertIn("does not exist", reason)

    async def test_slide_path_is_directory(self):
        params = dict(self.valid_params)
        params["slide_path"] = tempfile.gettempdir()

        ok, reason = await core.large_files_upload_package(**params)

        self.assertFalse(ok)
        self.assertIn("not a file", reason)

    async def test_empty_upload_directory(self):
        params = dict(self.valid_params)
        params["upload_directory"] = ""

        ok, reason = await core.large_files_upload_package(**params)

        self.assertFalse(ok)
        self.assertIn("upload_directory", reason)

    async def test_upload_directory_not_string(self):
        params = dict(self.valid_params)
        params["upload_directory"] = 42

        ok, reason = await core.large_files_upload_package(**params)

        self.assertFalse(ok)
        self.assertIn("upload_directory", reason)

    # =========================
    # SMOKE TEST (VALIDATION PASSES)
    # =========================

    async def test_validation_passes_until_upload_header(self):
        async def fake_upload_header(*args, **kwargs):
            raise RuntimeError("stop after validation")

        # patch method manually (no pytest monkeypatch!)
        original = core.PmaCoreClient.upload_header
        core.PmaCoreClient.upload_header = fake_upload_header

        try:
            ok, reason = await core.large_files_upload_package(**self.valid_params)

            self.assertFalse(ok)
            self.assertIn("stop after validation", reason)
        finally:
            core.PmaCoreClient.upload_header = original

    # SUCCESS TEST
    async def test_upload_success(self):
        async def fake_upload_header(*args, **kwargs):
            class FakeHeader:
                id = "fake_id"
                upload_type = "direct"
                urls = []
                multipart_files = []

            return FakeHeader()

        async def fake_upload_file(*args, **kwargs):
            return None

        async def fake_get_upload_status(*args, **kwargs):
            return True

        # patch
        orig_upload_header = core.PmaCoreClient.upload_header
        orig_upload_file = core.PmaCoreClient.upload_file
        orig_status = core.PmaCoreClient.get_upload_status

        core.PmaCoreClient.upload_header = fake_upload_header
        core.PmaCoreClient.upload_file = fake_upload_file
        core.PmaCoreClient.get_upload_status = fake_get_upload_status

        try:
            ok, reason = await core.large_files_upload_package(**self.valid_params)
            self.assertTrue(ok)
            self.assertIsNone(reason)
        finally:
            core.PmaCoreClient.upload_header = orig_upload_header
            core.PmaCoreClient.upload_file = orig_upload_file
            core.PmaCoreClient.get_upload_status = orig_status

    # PROGRESS CALLBACK TEST
    async def test_progress_callback_called(self):
        calls = []

        def progress_cb(ev):
            calls.append(ev.bytes_sent)

        async def fake_upload_header(*args, **kwargs):
            class FakeHeader:
                id = "fake_id"
                upload_type = "direct"
                urls = []
                multipart_files = []

            return FakeHeader()

        async def fake_upload_file(*args, **kwargs):
            cb = kwargs.get("progress_callback")
            if cb:
                cb(type("Ev", (), {
                    "bytes_sent": 50,
                    "total_bytes": 100,
                    "percent": 50.0,
                    "part_number": 1,
                    "file_path": "test"
                })())
                cb(type("Ev", (), {
                    "bytes_sent": 100,
                    "total_bytes": 100,
                    "percent": 100.0,
                    "part_number": 1,
                    "file_path": "test"
                })())

        async def fake_get_upload_status(*args, **kwargs):
            return True

        orig_upload_header = core.PmaCoreClient.upload_header
        orig_upload_file = core.PmaCoreClient.upload_file
        orig_status = core.PmaCoreClient.get_upload_status

        core.PmaCoreClient.upload_header = fake_upload_header
        core.PmaCoreClient.upload_file = fake_upload_file
        core.PmaCoreClient.get_upload_status = fake_get_upload_status

        try:
            params = dict(self.valid_params)
            params["progress_callback"] = progress_cb

            ok, _ = await core.large_files_upload_package(**params)

            self.assertTrue(ok)
            self.assertGreater(len(calls), 0)
            self.assertEqual(calls[-1], 100)
        finally:
            core.PmaCoreClient.upload_header = orig_upload_header
            core.PmaCoreClient.upload_file = orig_upload_file
            core.PmaCoreClient.get_upload_status = orig_status

    # CANCEL / TIMEOUT TEST
    async def test_upload_timeout(self):
        async def fake_upload_header(*args, **kwargs):
            await asyncio.sleep(5)  # имитация зависания

        orig_upload_header = core.PmaCoreClient.upload_header
        core.PmaCoreClient.upload_header = fake_upload_header

        try:
            with self.assertRaises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    core.large_files_upload_package(**self.valid_params),
                    timeout=0.5
                )
        finally:
            core.PmaCoreClient.upload_header = orig_upload_header


if __name__ == "__main__":
    unittest.main()
