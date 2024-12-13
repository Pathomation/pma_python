import unittest
from pma_python import core_admin
from pma_python import core

class CoreTest(unittest.TestCase):

    def setUp(self):
        self.core3 = "https://snapshot.pathomation.com/PMA.core/3.0.3/"
        self.username = "vitalij"
        self.password = "PMI9GH9I"
        self.local_file1 = "C:\\Users\\VitalijVictorPathoma\\Downloads\\part.tif"
        self.local_file2 = "C:/Slides/14.svs"
        self.local_file3 = "C:/Slides/CMU-1.mrxs"
        self.core_file1 = "_sys_aws_s3/alignment/casus001/casus001_HE_1.mrxs"
        self.core_file2 = "_sys_aws_s3/brightfield/Test_slide_pathomation_admin.svs"
        self.core_file3 = "_sys_aws_s3/2DollarBill.zif"
        self._pma_pmacoreliteURL = "http://localhost:54001/"
        self.first_n_em_dir = "_sys_aws_s3/annotations"
        self.label_url = "https://snapshot.pathomation.com/PMA.core/3.0.3/barcode?SessionID=NjpybCWmdMJfCTRNdqa7PA2&pathOrUid=_sys_aws_s3%2Falignment%2Fcasus001%2Fcasus001_HE_1.mrxs&w=300&h=150"
        self.barcode_text = ['UZBrussel23B6793-A-1-1HE']
        self.thumbnail_url = "https://snapshot.pathomation.com/PMA.core/3.0.3/thumbnail?SessionID=NjpybCWmdMJfCTRNdqa7PA2&pathOrUid=_sys_aws_s3%2Falignment%2Fcasus001%2Fcasus001_HE_1.mrxs&w=150&h=150"
        self.macro_url = 'https://snapshot.pathomation.com/PMA.core/3.0.3/macro?SessionID=NjpybCWmdMJfCTRNdqa7PA2&pathOrUid=_sys_aws_s3%2Falignment%2Fcasus001%2Fcasus001_HE_1.mrxs&w=200&h=200'
        self.tile_url = 'https://snapshot.pathomation.com/PMA.core/3.0.3/tile?sessionID=NjpybCWmdMJfCTRNdqa7PA2&channels=0&timeframe=0&layer=0&pathOrUid=_sys_aws_s3%2Falignment%2Fcasus001%2Fcasus001_HE_1.mrxs&x=10&y=20&z=2&format=png&quality=90&cache=true'
        self.tmp_upload_dir = "_sys_aws_s3/alignment/X_Set_1"
        self.tmp_download_dir = "C:\\Users\\VitalijVictorPathoma\\Downloads"
        self.session_id = core_admin.admin_connect(self.core3, self.username, self.password)

    def test_set_debug_flag(self):
        flag = core_admin.set_debug_flag(flag=False)
        print(flag)
        self.assertIsNone(flag)

    def test_pma_admin_url(self):
        result = core_admin._pma_admin_url(sessionID=self.session_id)
        print(result)
        self.assertIsInstance(result, str)
        self.assertTrue(result.endswith("admin/json/"))

    def test_pma_check_for_pma_start(self):
        self.assertRaises(
            Exception,
            core_admin._pma_check_for_pma_start,
            method="test_method",
            url=None,
            session=core._pma_pmacoreliteSessionID
        )
        self.assertRaises(
            ValueError,
            core_admin._pma_check_for_pma_start,
            method="test_method",
            url=core._pma_pmacoreliteURL,
            session=None
        )

    def test_pma_http_post(self):
        url = self.core3
        data = {"key": "value"}
        result = core_admin._pma_http_post(url, data, verify=True)
        print(result)
        self.assertIsInstance(result, str)

    def test_admin_connect(self):
        result = core_admin.admin_connect(
            pmacoreURL=self.core3,
            pmacoreAdmUsername=self.username,
            pmacoreAdmPassword=self.password
        )
        print(result)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_send_email_reminder(self):
        result = core_admin.send_email_reminder(
            admSessionID=self.session_id,
            login=self.username,
            subject="PMA.core password reminder"
        )
        self.assertIsInstance(result, str)

    def test_add_user(self):
        admSessionID = self.session_id
        login = "test_user"
        firstName = "Test"
        lastName = "User"
        email = "test_user@example.com"
        pwd = "password"

        result = core_admin.add_user(
            admSessionID=admSessionID,
            login=login,
            firstName=firstName,
            lastName=lastName,
            email=email,
            pwd=pwd,
            canAnnotate=True,
            isAdmin=True,
            isSuspended=False
        )
        print(result)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_user_exists(self):
        result = core_admin.user_exists(
            admSessionID=self.session_id,
            u=self.username
        )
        print(result)
        self.assertIsInstance(result, bool)

    def test_create_amazons3_mounting_point(self):
        result = core_admin.create_amazons3_mounting_point(
            accessKey="test_access_key",
            secretKey="test_secret_key",
            path="/test_path",
            instanceId="test_instance_id",
            chunkSize=1024,
            serviceUrl="http://test-service-url.com"
        )
        print(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["AccessKey"], "test_access_key")

    def test_create_filesystem_mounting_point(self):
        result = core_admin.create_filesystem_mounting_point(
            username="test_user",
            password="test_password",
            domainName="test_domain",
            path="/test_path",
            instanceId="test_instance_id"
        )
        print(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["Username"], "test_user")

    def test_create_onedrive_mounting_point(self):
        result = core_admin.create_onedrive_mounting_point()
        print(result)
        self.assertIsNone(result)

    def test_create_dropbox_mounting_point(self):
        result = core_admin.create_dropbox_mounting_point()
        print(result)
        self.assertIsNone(result)

    def test_create_googledrive_mounting_point(self):
        result = core_admin.create_googledrive_mounting_point()
        print(result)
        self.assertIsNone(result)

    def test_create_root_directory(self):
        result = core_admin.create_root_directory(
            admSessionID=self.session_id,
            alias="test_root",
            description="Test root directory",
            isPublic=True
        )
        print(result)
        self.assertIsInstance(result, str)

    def test_create_directory(self):
        admSessionID = "test_admin_session"
        path = "/test_directory"
        result = core_admin.create_directory(admSessionID, path)
        print(result)
        self.assertIsInstance(result, bool)

    def test_rename_directory(self):
        admSessionID = "test_admin_session"
        originalPath = "/test_directory"
        newName = "renamed_directory"
        result = core_admin.rename_directory(admSessionID, originalPath, newName)
        print(result)
        self.assertTrue(result)

    def test_delete_directory(self):
        admSessionID = "test_admin_session"
        path = "/test_directory"
        result = core_admin.delete_directory(admSessionID, path)
        print(result)
        self.assertTrue(result)

    def test_delete_slide(self):
        admSessionID = "test_admin_session"
        slideRef = "/test_slide"
        result = core_admin.delete_slide(admSessionID, slideRef)
        print(result)
        self.assertTrue(result)

    def test_reverse_uid(self):
        admSessionID = "test_admin_session"
        slideRefUid = "unique-id-123"
        result = core_admin.reverse_uid(admSessionID, slideRefUid)
        print(result)
        self.assertIsInstance(result, str)

    def test_reverse_root_directory(self):
        admSessionID = "test_admin_session"
        alias = "test_root"
        result = core_admin.reverse_root_directory(admSessionID, alias)
        print(result)
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()
