import unittest
import devopsctl

class TestDevOpsCtl(unittest.TestCase):

    def test_for_build_def_input(self):
        with self.assertRaises(TypeError):
            devopsctl.get_kpi_pipeline_runs_count("string")
    
    def test_average(self):
        self.assertEqual(devopsctl.get_average(total=50, count=2), 25)
        self.assertEqual(devopsctl.get_average(total=2, count=2), 1)
        self.assertEqual(devopsctl.get_average(total=1, count=1), 1)

        with self.assertRaises(TypeError):
            devopsctl.get_average("string",1)
            devopsctl.get_average(10.111,1)
        
        with self.assertRaises(ValueError):
            devopsctl.get_average(1,0)


if __name__ == '__main__':
    unittest.main()