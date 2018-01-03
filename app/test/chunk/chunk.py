import unittest
import tempfile
import shutil


class ChunkTest(unittest.TestCase):

    def setUp(self):
        self.working_directory = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.working_directory)

    def test_chunk_by_line(self):
        pass
