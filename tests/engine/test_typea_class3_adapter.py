import unittest

from engine.prowrap_calculations import (
    apply_type_a_class3_result_to_repair,
    calculate_repair,
    calculate_type_a_class3_prowrap_check,
    substrate_credit_bar_for_iso_check,
)
from engine.prowrap_materials import PROWRAP


class TypeAClass3AdapterTest(unittest.TestCase):
    def test_adapter_maps_app_inputs_and_prowrap_data_to_typea_class3_route(self):
        result = calculate_type_a_class3_prowrap_check(
            od=457.2,
            pressure_bar=50.0,
            temp=40.0,
            rem_wall=4.5,
            design_life=20,
            substrate_allowable_pressure_bar=0.0,
            installation_temp=20.0,
            component_type="Straight",
            cyclic_derating_factor=1.0,
        )

        self.assertEqual(result["circumferential_strain_basis"], "performance_data")
        self.assertAlmostEqual(result["peq_mpa"], 5.0)
        self.assertAlmostEqual(result["long_term_strain_lcl"], PROWRAP["long_term_strain_20y"])
        self.assertAlmostEqual(result["input_summary"]["pressure_bar"], 50.0)
        self.assertAlmostEqual(result["input_summary"]["substrate_allowable_pressure_bar"], 0.0)
        self.assertAlmostEqual(result["input_summary"]["lap_shear_mpa"], PROWRAP["long_term_lap_shear"])
        self.assertAlmostEqual(result["input_summary"]["hoop_modulus_mpa"], PROWRAP["modulus_circ"])
        self.assertIn("Formula 11 performance route", result["input_summary"]["performance_data"])
        self.assertGreater(result["tdesign_final_mm"], 0)
        self.assertGreaterEqual(result["layer_count"], 1)

    def test_performance_route_uses_prowrap_eps_lt(self):
        result = calculate_type_a_class3_prowrap_check(
            od=457.2,
            pressure_bar=50.0,
            temp=40.0,
            rem_wall=4.5,
            design_life=20,
        )
        # Formula 11: eps_c = fperf * fT2 * eps_lt (design-life data, Class 3)
        eps_lt = PROWRAP["long_term_strain_lcl"]
        fperf = 0.76 * 10 ** (-0.00273 * 20)
        delta = PROWRAP["max_temp"] - 40.0  # Ttest == Tamb in the adapter
        ft2 = 0.0000625 * delta**2 + 0.00125 * delta + 0.7
        self.assertAlmostEqual(result["eps_c"], fperf * ft2 * eps_lt, places=9)

    def test_cyclic_factor_applies_on_performance_route(self):
        base = calculate_type_a_class3_prowrap_check(
            od=457.2, pressure_bar=50.0, temp=40.0, rem_wall=4.5, design_life=20,
        )
        derated = calculate_type_a_class3_prowrap_check(
            od=457.2, pressure_bar=50.0, temp=40.0, rem_wall=4.5, design_life=20,
            cyclic_derating_factor=0.5,
        )
        self.assertAlmostEqual(derated["eps_c"], 0.5 * base["eps_c"], places=9)

    def test_axial_load_case_selector(self):
        import math

        # Case 0 (default): buried restrained pipeline - axial loads not
        # taken into account.
        iso = calculate_type_a_class3_prowrap_check(
            od=457.2, pressure_bar=50.0, temp=40.0, rem_wall=4.5,
            design_life=20, nominal_wall_mm=9.53,
        )
        self.assertEqual(iso["feq_n"], 0.0)
        self.assertEqual(iso["tmin_a_mm"], 0.0)

        # Case 1: severed-pipe/above-ground - axial loads per ISO
        # Formula 4 (pressure end-thrust).
        iso1 = calculate_type_a_class3_prowrap_check(
            od=457.2, pressure_bar=50.0, temp=40.0, rem_wall=4.5,
            design_life=20, nominal_wall_mm=9.53, axial_load_case=1,
        )
        self.assertAlmostEqual(
            iso1["feq_n"], 5.0 * math.pi * 457.2**2 / 4.0
        )
        self.assertGreater(iso1["tmin_a_mm"], 0.0)

    def test_iso_result_can_drive_displayed_repair_metrics_when_pressure_deficit_exists(self):
        # 110 bar exceeds the B31G safe pressure (P_S = 9.95 MPa), so a
        # genuine pressure deficit exists and the ISO result controls.
        repair = calculate_repair(
            customer="PROTAP",
            location="Turkey",
            report_no="24-152",
            od=457.2,
            wall=9.53,
            pressure=110.0,
            temp=40.0,
            defect_type="Corrosion",
            defect_loc="External",
            length=100.0,
            rem_wall=4.5,
            yield_strength=359.0,
            design_factor=0.72,
            design_life=20,
        )
        iso_result = calculate_type_a_class3_prowrap_check(
            od=457.2,
            pressure_bar=110.0,
            temp=40.0,
            rem_wall=4.5,
            design_life=20,
            substrate_allowable_pressure_bar=substrate_credit_bar_for_iso_check(repair),
            nominal_wall_mm=9.53,
        )

        updated = apply_type_a_class3_result_to_repair(repair, iso_result)

        self.assertFalse(repair["b31g_details"]["acceptable"])
        self.assertGreater(repair["p_composite_design"], 0)
        # Restrained-pipeline axial basis (no end-thrust): circumferential
        # requirement 1.92 mm -> 2 mm / 2-layer floor -> 3 plies.
        self.assertEqual(updated["num_plies"], 3)
        self.assertTrue(updated["iso_typea_class3_controls"])
        self.assertAlmostEqual(updated["t_required"], iso_result["tdesign_final_mm"])
        self.assertAlmostEqual(updated["final_thickness"], 3 * PROWRAP["ply_thickness"])
        self.assertAlmostEqual(updated["overlap_length"], iso_result["lover_required_mm"])
        self.assertAlmostEqual(
            updated["iso_length"],
            100.0
            + 2 * iso_result["lover_required_mm"]
            + 2 * iso_result["taper_length_mm"],
        )
        self.assertEqual(updated["num_bands"], 2)
        self.assertEqual(updated["proc_length"], 600)

    def test_controlling_result_uses_requested_dual_widths_without_structural_drift(self):
        structural_keys = (
            "t_required",
            "num_plies",
            "final_thickness",
            "overlap_length",
            "taper_length",
            "iso_length",
            "p_steel_capacity",
            "p_composite_design",
            "b31g_details",
            "b31g_assessments",
            "type_b_details",
            "thickness_check_ok",
            "compliance_warnings",
            "iso_typea_class3_controls",
            "iso_typea_class3_noncontrolling_reason",
        )
        repair = calculate_repair(
            customer="PROTAP",
            location="Turkey",
            report_no="24-152",
            od=457.2,
            wall=9.53,
            pressure=110.0,
            temp=40.0,
            defect_type="Corrosion",
            defect_loc="External",
            length=100.0,
            rem_wall=4.5,
            yield_strength=359.0,
            design_factor=0.72,
            design_life=20,
            cloth_widths_mm=(300.0, 300.0),
        )
        iso_result = calculate_type_a_class3_prowrap_check(
            od=457.2,
            pressure_bar=110.0,
            temp=40.0,
            rem_wall=4.5,
            design_life=20,
            substrate_allowable_pressure_bar=substrate_credit_bar_for_iso_check(repair),
            nominal_wall_mm=9.53,
        )
        cases = (
            (
                (300.0, 300.0),
                (
                    0, 2, 2, 600.0, 550.0, 161.066183983945,
                    2.585405090198256, 3.1024861082379074,
                ),
            ),
            (
                (500.0, 500.0),
                (
                    1, 0, 1, 500.0, 500.0, 111.066183983945,
                    2.15450424183188, 2.585405090198256,
                ),
            ),
            (
                (300.0, 500.0),
                (
                    1, 0, 1, 500.0, 500.0, 111.066183983945,
                    2.15450424183188, 2.585405090198256,
                ),
            ),
            (
                (500.0, 300.0),
                (
                    1, 0, 1, 500.0, 500.0, 111.066183983945,
                    2.15450424183188, 2.585405090198256,
                ),
            ),
        )
        updated_results = []
        for widths, expected_procurement in cases:
            with self.subTest(widths=widths):
                updated = apply_type_a_class3_result_to_repair(
                    repair, iso_result, cloth_widths_mm=widths,
                )
                self.assertTrue(updated["iso_typea_class3_controls"])
                self.assertEqual(
                    (
                        updated["num_bands_500"],
                        updated["num_bands_300"],
                        updated["num_bands"],
                        updated["proc_length"],
                        updated["covered_length_mm"],
                        updated["excess_coverage_mm"],
                        updated["optimized_sqm"],
                        updated["epoxy_kg"],
                    ),
                    expected_procurement,
                )
                self.assertEqual(
                    updated["cloth_widths_mm"], tuple(sorted(widths)),
                )
                updated_results.append(updated)

        baseline = {
            key: updated_results[0][key]
            for key in structural_keys
        }
        for updated in updated_results[1:]:
            self.assertEqual(
                {key: updated[key] for key in structural_keys},
                baseline,
            )

    def test_external_non_leak_crack_uses_effective_pipe_capacity_as_substrate_credit(self):
        repair = calculate_repair(
            customer="PROTAP",
            location="Turkey",
            report_no="24-152",
            od=457.2,
            wall=9.53,
            pressure=50.0,
            temp=40.0,
            defect_type="Corrosion",
            defect_loc="External",
            length=100.0,
            rem_wall=4.5,
            yield_strength=359.0,
            design_factor=0.72,
            design_life=20,
        )

        credit_bar = substrate_credit_bar_for_iso_check(repair)
        iso_result = calculate_type_a_class3_prowrap_check(
            od=457.2,
            pressure_bar=50.0,
            temp=40.0,
            rem_wall=4.5,
            design_life=20,
            substrate_allowable_pressure_bar=credit_bar,
            nominal_wall_mm=9.53,
        )
        updated = apply_type_a_class3_result_to_repair(repair, iso_result)

        self.assertAlmostEqual(credit_bar, repair["p_steel_capacity"] * 10.0)
        # B31G Modified P_S = 9.95 MPa -> 99.5 bar substrate credit.
        self.assertAlmostEqual(credit_bar, 99.51873620726573)
        # Substrate covers the pressure and no axial load is applied
        # (restrained pipeline): minimum-thickness floor governs.
        self.assertEqual(iso_result["layer_count"], 3)
        self.assertEqual(updated["num_plies"], 3)
        self.assertFalse(updated["iso_typea_class3_controls"])
        self.assertEqual(updated["iso_typea_class3_noncontrolling_reason"], "effective_pipe_capacity_covers_design_pressure")
        self.assertAlmostEqual(
            iso_result["input_summary"]["substrate_allowable_pressure_bar"],
            credit_bar,
        )

    def test_leak_and_crack_do_not_get_substrate_credit(self):
        for defect_type in ["Leak", "Crack"]:
            with self.subTest(defect_type=defect_type):
                repair = calculate_repair(
                    customer="PROTAP",
                    location="Turkey",
                    report_no="24-152",
                    od=457.2,
                    wall=9.53,
                    pressure=50.0,
                    temp=40.0,
                    defect_type=defect_type,
                    defect_loc="External",
                    length=100.0,
                    rem_wall=4.5,
                    yield_strength=359.0,
                    design_factor=0.72,
                    design_life=20,
                )

                self.assertEqual(substrate_credit_bar_for_iso_check(repair), 0.0)

    def test_internal_corrosion_projected_to_end_of_life(self):
        base = dict(
            customer="PROTAP", location="Turkey", report_no="24-152",
            od=457.2, wall=9.53, pressure=50.0, temp=40.0,
            defect_type="Corrosion", defect_loc="Internal", length=100.0,
            rem_wall=4.5, yield_strength=359.0, design_factor=0.72,
            design_life=20,
        )
        # Internal defects follow the Type B route (no substrate pressure
        # credit); the wall is still projected to end of life and the B31G
        # assessment is retained for information.
        r = calculate_repair(**base, internal_corrosion_rate=0.1)
        self.assertAlmostEqual(r["rem_wall_eol"], 2.5)
        self.assertEqual(r["calc_method_thick"], "Type B (Total Replacement)")
        self.assertAlmostEqual(r["p_steel_capacity"], 0.0)
        self.assertEqual(substrate_credit_bar_for_iso_check(r), 0.0)
        self.assertIsNotNone(r["b31g_details"])

        # Projected below 1 mm -> Type B, no substrate credit.
        r2 = calculate_repair(**base, internal_corrosion_rate=0.2)
        self.assertAlmostEqual(r2["rem_wall_eol"], 0.5)
        self.assertEqual(r2["calc_method_thick"], "Type B (Total Replacement)")
        self.assertEqual(substrate_credit_bar_for_iso_check(r2), 0.0)

        # Rate 0 on an internal defect must raise a warning prompting for
        # a corrosion rate.
        r3 = calculate_repair(**base)
        self.assertTrue(
            any("corrosion rate = 0" in w for w in r3["compliance_warnings"])
        )


if __name__ == "__main__":
    unittest.main()
