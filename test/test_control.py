import unittest
from pma_python import core_admin
from pma_python import core
from pma_python import control

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
        self.pmacontrolURL = "https://host.pathomation.com/pma.control.2/"
        self.pmacontrolProjectID = 1001
        self.pmacontrolCaseCollectionID = 2001
        self.pmacontrolTrainingSessionID = 3001
        self.pmacontrolCaseID = 4001
        self.titleSubstring = "Test"
        self.session_id = core_admin.admin_connect(self.core3, self.username, self.password)

    def test_set_debug_flag(self):
        flag = control.set_debug_flag(flag=False)
        print(flag)
        self.assertIsNone(flag)

    def test_get_version_info(self):
        result = control.get_version_info(self.pmacontrolURL)
        print(result)
        self.assertEqual(result, "2.0.0.1419")

    def test_pma_get_training_sessions(self):
        result = control._pma_get_training_sessions(self.pmacontrolURL, self.session_id)
        print(result)
        self.assertEqual(result, {'Message': 'Authorization has been denied for this request.'})

    def test_pma_format_training_session_properly(self):
        sess = {
            "Id": 1,
            "Title": "Test Session",
            "LogoPath": "/path/to/logo",
            "StartsOn": "2024-01-01T00:00:00",
            "EndsOn": "2024-01-02T00:00:00",
            "ProjectId": 1001,
            "State": "Active",
            "Participants": [{"Id": 1}, {"Id": 2}],
            "CaseCollections": [
                {"CaseCollectionId": 1, "Title": "Collection 1", "Url": "/url1"},
                {"CaseCollectionId": 2, "Title": "Collection 2", "Url": "/url2"}
            ]
        }
        result = control._pma_format_training_session_properly(sess)
        print(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["Id"], 1)
        self.assertEqual(result["NumberOfParticipants"], 2)
        self.assertIn("CaseCollections", result)

    def test_get_training_sessions_for_participant(self):
        result = control.get_training_sessions_for_participant(
            self.pmacontrolURL, self.username, self.session_id
        )
        print(result)
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)

    def test_get_training_session_participants(self):
        pmacontrolTrainingSessionID = 1
        result = control.get_training_session_participants(
            self.pmacontrolURL, pmacontrolTrainingSessionID, self.session_id)
        print(result)
        self.assertIsInstance(result, dict)

    def test_is_participant_in_training_session(self):
        pmacontrolTrainingSessionID = 1
        result = control.is_participant_in_training_session(
            self.pmacontrolURL, self.username, pmacontrolTrainingSessionID, self.session_id
        )
        print(result)
        self.assertIsInstance(result, bool)

    def test_get_training_session_url(self):
        pmacontrolTrainingSessionID = 1
        pmacontrolCaseCollectionID = 101
        result = control.get_training_session_url(
            self.pmacontrolURL, self.session_id, self.username, pmacontrolTrainingSessionID,
            pmacontrolCaseCollectionID, self.session_id
        )
        print(result)
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("http"))

    def test_get_all_participants(self):
        result = control.get_all_participants(self.pmacontrolURL, self.session_id)
        print(result)
        self.assertIsInstance(result, dict)

    def test_register_participant_for_training_session(self):
        pmacontrolTrainingSessionID = 1
        pmacontrolRole = "Viewer"

        result = control.register_participant_for_training_session(
            self.core3,
            self.username,
            pmacontrolTrainingSessionID,
            pmacontrolRole,
            self.session_id
        )
        print(result)
        self.assertIsNotNone(result)

    def test_register_participant_for_project(self):
        pmacontrolProjectID = 101
        pmacontrolRole = "Editor"
        pmacoreSessionID = "test_session_id"

        result = control.register_participant_for_project(
            self.pmacontrolURL,
            self.username,
            pmacontrolProjectID,
            pmacontrolRole,
            pmacoreSessionID
        )
        print(result)
        self.assertIsNotNone(result)

    def test_set_participant_interactionmode(self):
        pmacontrolTrainingSessionID = 1
        pmacontrolCaseCollectionID = 101
        pmacontrolInteractionMode = "Unlocked"

        result = control.set_participant_interactionmode(
            self.pmacontrolURL,
            self.username,
            pmacontrolTrainingSessionID,
            pmacontrolCaseCollectionID,
            pmacontrolInteractionMode,
            self.session_id
        )
        print(result)
        self.assertIsNotNone(result)

    def test_pma_get_case_collection_training_session_id(self):
        pmacontrolTrainingSessionID = 1
        pmacontrolCaseCollectionID = 101

        result = control._pma_get_case_collection_training_session_id(
            self.pmacontrolURL,
            pmacontrolTrainingSessionID,
            pmacontrolCaseCollectionID,
            self.session_id
        )
        print(result)
        self.assertIsInstance(result, int)

    def test_set_participant_interactionmode(self):
        pmacontrolTrainingSessionID = 1
        pmacontrolCaseCollectionID = 101
        pmacontrolInteractionMode = "Unlocked"

        result = control.set_participant_interactionmode(
            self.pmacontrolURL,
            self.username,
            pmacontrolTrainingSessionID,
            pmacontrolCaseCollectionID,
            pmacontrolInteractionMode,
            self.session_id
        )
        self.assertIsNotNone(result)
        print(result)

    def test_get_training_session_titles(self):
        pmacontrolProjectID = 1001
        result = control.get_training_session_titles(
            self.pmacontrolURL, pmacontrolProjectID, self.session_id
        )
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        print(result)

    def test_get_training_session_titles_dict(self):
        pmacontrolProjectID = 1001
        result = control.get_training_session_titles_dict(
            self.pmacontrolURL, pmacontrolProjectID, self.session_id
        )
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        print(result)

    def test_get_training_sessions(self):
        pmacontrolProjectID = 1001
        result = control.get_training_sessions(
            self.pmacontrolURL, pmacontrolProjectID, self.session_id
        )
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        print(result)

    def test_get_training_session(self):
        result = control.get_training_session(self.pmacontrolURL, self.pmacontrolTrainingSessionID, self.session_id)
        self.assertIsNotNone(result)
        print(result)

    def test_search_training_session(self):
        result = control.search_training_session(self.pmacontrolURL, self.titleSubstring, self.session_id)
        self.assertIsNotNone(result)
        print(result)

    def test_get_case_collections(self):
        result = control.get_case_collections(self.pmacontrolURL, self.pmacontrolProjectID, self.session_id)
        self.assertIsInstance(result, dict)
        print(result)

    def test_get_case_collection_titles(self):
        result = control.get_case_collection_titles(self.pmacontrolURL, self.pmacontrolProjectID, self.session_id)
        self.assertIsInstance(result, list)
        print(result)

    def test_get_project(self):
        result = control.get_project(self.pmacontrolURL, self.pmacontrolProjectID, self.session_id)
        self.assertIsNotNone(result)
        print(result)

    def test_search_project(self):
        result = control.search_project(self.pmacontrolURL, self.titleSubstring, self.session_id)
        self.assertIsNotNone(result)
        print(result)

    def test_get_project_by_case_id(self):
        result = control.get_project_by_case_id(self.pmacontrolURL, self.pmacontrolCaseID, self.session_id)
        self.assertIsNotNone(result)
        print(result)

    def test_get_project_by_case_collection_id(self):
        result = control.get_project_by_case_collection_id(self.pmacontrolURL, self.pmacontrolCaseCollectionID,
                                                   self.session_id)
        self.assertIsNotNone(result)
        print(result)

    def test_get_training_session_titles(self):
        result = control.get_training_session_titles(self.pmacontrolURL, self.session_id)
        self.assertIsInstance(result, list)
        print(result)


if __name__ == "__main__":
    unittest.main()
