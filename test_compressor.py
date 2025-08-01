import os
import unittest
import shutil
from compressor_app import compress_file

class TestCompressor(unittest.TestCase):
    def test_compress_sample(self):
        sample = os.path.join('testdata', 'Box', 'glTF_Binary', 'Box.glb')
        if not shutil.which('gltf-pipeline') or not shutil.which('assimp'):
            self.skipTest('gltf-pipeline or assimp unavailable')
        if not os.path.exists(sample):
            self.skipTest('sample glb missing')
        out = compress_file(sample)
        self.assertTrue(os.path.exists(out))
        self.assertLess(os.path.getsize(out), 3*1024*1024)

if __name__ == '__main__':
    unittest.main()
