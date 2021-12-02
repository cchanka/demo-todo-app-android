import unittest
import devopsctl

class TestDevOpsCtl(unittest.TestCase):

    def test_for_build_def_input(self):
        with self.assertRaises(TypeError):
            devopsctl.get_kpi_pipeline_runs_count("string")


if __name__ == '__main__':
    unittest.main()