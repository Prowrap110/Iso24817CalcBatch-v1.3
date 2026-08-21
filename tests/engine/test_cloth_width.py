import unittest

from engine.prowrap_calculations import calculate_repair
from tests.engine.test_current_calculation_baseline import default_inputs


class ClothWidthTest(unittest.TestCase):
    def test_300_mm_width_preserves_baseline_procurement(self):
        result = calculate_repair(**default_inputs(), cloth_width_mm=300.0)

        self.assertEqual(result["num_bands"], 2)
        self.assertEqual(result["proc_length"], 600.0)
        self.assertAlmostEqual(result["optimized_sqm"], 2.585405090198256)

    def test_approved_width_pairs_change_only_procurement_outputs(self):
        results = tuple(
            calculate_repair(**default_inputs(), cloth_widths_mm=widths)
            for widths in (
                (300.0, 300.0),
                (500.0, 500.0),
                (300.0, 500.0),
                (500.0, 300.0),
            )
        )
        structural_keys = (
            "t_required", "num_plies", "final_thickness", "overlap_length",
            "taper_length", "iso_length", "p_steel_capacity",
            "p_composite_design", "b31g_details", "b31g_assessments",
            "type_b_details", "thickness_check_ok", "compliance_warnings",
        )
        baseline = {key: results[0][key] for key in structural_keys}

        self.assertEqual(
            tuple((item["num_bands_500"], item["num_bands_300"], item["proc_length"])
                  for item in results),
            ((0, 2, 600.0), (1, 0, 500.0), (1, 0, 500.0), (1, 0, 500.0)),
        )
        for result in results[1:]:
            self.assertEqual(
                {key: result[key] for key in structural_keys}, baseline,
            )

    def test_unapproved_widths_are_rejected_by_the_pinned_optimizer(self):
        for widths in ((250.0, 300.0), (0.0, 300.0), (50.0, 50.0)):
            with self.subTest(widths=widths):
                with self.assertRaisesRegex(ValueError, "Cloth widths"):
                    calculate_repair(**default_inputs(), cloth_widths_mm=widths)


if __name__ == "__main__":
    unittest.main()
