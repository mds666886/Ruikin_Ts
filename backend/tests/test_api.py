import tempfile
import unittest
from pathlib import Path

from app import create_app
from app.models.db import db


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
                "UPLOAD_DIR": str(Path(self.tempdir.name) / "uploads"),
            }
        )
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.tempdir.cleanup()

    def test_health(self):
        resp = self.client.get('/api/health')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['code'], 0)

    def test_bootstrap_and_scene(self):
        r = self.client.post('/api/projects/bootstrap_demo')
        self.assertEqual(r.status_code, 200)
        data = r.get_json()['data']

        parse = self.client.post(f"/api/analysis/parse/{data['file_id']}")
        self.assertEqual(parse.status_code, 200)

        scene = self.client.post(f"/api/scene/rewrite/{data['project_id']}", json={'scene_type': 'competition'})
        self.assertEqual(scene.status_code, 200)

        scene_list = self.client.get(f"/api/scene/project/{data['project_id']}")
        self.assertEqual(scene_list.status_code, 200)
        self.assertGreater(len(scene_list.get_json()['data']), 0)

    def test_invalid_scene_type(self):
        create = self.client.post('/api/projects', json={'name': 'x', 'scene_type': 'invalid'})
        self.assertEqual(create.status_code, 400)


if __name__ == '__main__':
    unittest.main()
