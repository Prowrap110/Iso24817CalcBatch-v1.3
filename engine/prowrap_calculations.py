"""Pure calculation functions for the PROWRAP repair calculator."""

import math

from .band_procurement import optimize_band_procurement
from .b31g import assess_b31g
from .corrosion_defects import (
    ACTUAL_DEFECT_LENGTH,
    build_corrosion_assessment_plan,
)
from .iso24817_typea_class3 import TypeAClass3Inputs, calculate_type_a_class3
from .prowrap_materials import PROWRAP
from .prowrap_mechanisms import DENT_NO_CRACK, DENT_WITH_CRACK, normalize_mechanism

# Carbon-steel substrate CTE used in the ISO 24817 Formula (10)
# thermal-mismatch term (same value as the rigorous module default).
STEEL_CTE_PER_C = 12e-6

# ISO 24817 Table 12 stress-concentration factors f_th by component type.
COMPONENT_FTH = {
    "": 1.0,
    "STRAIGHT": 1.0,
    "PIPE": 1.0,
    "STRAIGHT PIPE": 1.0,
    "BEND": 1.2,
    "TEE": 2.0,
    "FLANGE": 1.1,
    "REDUCER": 1.1,
}


def baseline_component_factor(component_type):
    key = (component_type or "Straight").strip().upper()
    if key not in COMPONENT_FTH:
        raise ValueError(
            "Unknown component type. Use Straight, Bend, Tee, Flange, or Reducer."
        )
    return COMPONENT_FTH[key]


def component_pipe_allowable_basis(
    *, od_mm, remaining_wall_mm, smys_mpa, design_factor,
):
    allowable_stress_mpa = smys_mpa * design_factor
    allowable_pressure_mpa = max(
        0.0,
        2.0 * allowable_stress_mpa * remaining_wall_mm / od_mm,
    )
    return {
        "allowable_stress_mpa": allowable_stress_mpa,
        "allowable_pressure_mpa": allowable_pressure_mpa,
    }


def baseline_type_a_design(
    od_mm,
    nominal_wall_mm,
    pressure_mpa,
    substrate_pressure_mpa,
    design_temp_c,
    installation_temp_c,
    design_life_years,
    component_type="Straight",
    cyclic_derating_factor=1.0,
    axial_load_case=0,
):
    """ISO 24817 Type A laminate design for the baseline route (closed form).

    Independent implementation of the same formulae as the rigorous
    iso24817_typea_class3 module (kept separate so the two routes can be
    cross-checked against each other):

    - Formula (4):  pressure end-thrust Feq = pi/4 * p * D^2 when
      axial_load_case == 1 (severed-pipe / above-ground); Feq = 0 for the
      buried restrained case (axial_load_case == 0).
    - Formula (11) performance route with the Formula (25) cyclic factor:
      eps_c = fc * fperf * fT2 * eps_lt (PRW110 design-life data, Class 3).
    - Formula (10): axial allowable strain with the installation-temperature
      thermal-mismatch term, eps_a = fc * (fT1*eps_a0 - |dT*(alpha_s - alpha_a)|).
    - Formula (5) hoop thickness (closed form, live pressure = 0) and the
      axial minimum thickness, taking the larger.
    - Table 12 component factor f_th (Bend 1.2, Tee 2.0, Flange/Reducer 1.1)
      applied to the base thickness; Formula (33) tee pressure cap.
    - 7.5.14 minimum thickness floor: greater of 2 layers or 2 mm.
    - Formula (21) load-transfer overlap on the base thickness and eps_a.
    """
    fth = baseline_component_factor(component_type)
    ec = PROWRAP["modulus_circ"]
    ea = PROWRAP["modulus_axial"]
    nu = PROWRAP["poisson_circ"]
    ply = PROWRAP["ply_thickness"]
    tau = PROWRAP["long_term_lap_shear"]
    eps_lt = PROWRAP.get("long_term_strain_lcl", PROWRAP.get("long_term_strain_20y"))

    fperf = 0.76 * 10 ** (-0.00273 * design_life_years)
    # fT1 == fT2 here: Ttest == Tamb in the PRW110 qualification, so both
    # Table 8 polynomials reduce to the same argument Tm - Td.
    ft_delta = PROWRAP["max_temp"] - design_temp_c
    ft = 0.0000625 * ft_delta**2 + 0.00125 * ft_delta + 0.7

    # Formula (11) + Formula (25) cyclic derating.
    eps_c = cyclic_derating_factor * fperf * ft * eps_lt

    # Formula (10) axial allowable with installation-temperature mismatch.
    if ea > 0.5 * ec:
        eps_a0 = 0.003061 * 10 ** (-0.0044 * design_life_years)
    else:
        eps_a0 = 0.001
    dt_install = design_temp_c - installation_temp_c
    alpha_a = PROWRAP["thermal_expansion_axial"] * 1e-6
    eps_a = cyclic_derating_factor * (
        ft * eps_a0 - abs(dt_install * (STEEL_CTE_PER_C - alpha_a))
    )

    if eps_c <= 0:
        raise ValueError("Calculated circumferential allowable strain is <= 0.")
    if eps_a <= 0:
        raise ValueError(
            "Calculated axial allowable strain is <= 0 (installation-to-design "
            "thermal mismatch and cyclic derating leave no axial strain margin)."
        )

    # Formula (4) end-thrust.
    if axial_load_case == 1:
        feq = pressure_mpa * math.pi * od_mm**2 / 4.0
    else:
        feq = 0.0

    # Formula (5), closed form (live pressure = 0): hoop minimum thickness.
    driving_load = pressure_mpa * od_mm / 2.0 + nu * feq / (math.pi * od_mm)
    resisting_load = substrate_pressure_mpa * od_mm / 2.0
    tmin_c = max(0.0, (driving_load - resisting_load) / (ec * eps_c))

    # Axial minimum thickness.
    tmin_a = max(
        0.0,
        (
            feq / (math.pi * od_mm * ea)
            - pressure_mpa * od_mm * nu / (2.0 * ec)
        )
        / eps_a,
    )

    tdesign_base = max(tmin_c, tmin_a)
    tdesign = tdesign_base * fth

    # Formula (33) tee pressure cap as a thickness requirement
    # (branch diameter conservatively taken equal to D).
    if (component_type or "").strip().upper() == "TEE":
        t_required_tee = pressure_mpa * (od_mm + od_mm) / (2.0 * ec * eps_c)
        tdesign = max(tdesign, t_required_tee)

    # 7.5.14 minimum laminate thickness (Type A).
    min_thickness_mm = max(2.0, 2.0 * ply)
    tdesign_final = max(tdesign, min_thickness_mm)

    # Formula (21) load transfer on the base (pre-f_th) thickness.
    lmin_transfer = 3.0 * ea * eps_a * tdesign_base / tau

    return {
        "substrate_pressure_mpa": substrate_pressure_mpa,
        "fperf": fperf,
        "ft": ft,
        "eps_lt": eps_lt,
        "eps_c": eps_c,
        "eps_a0": eps_a0,
        "eps_a": eps_a,
        "feq_n": feq,
        "tmin_c_mm": tmin_c,
        "tmin_a_mm": tmin_a,
        "tdesign_base_mm": tdesign_base,
        "fth_stress": fth,
        "min_thickness_floor_mm": min_thickness_mm,
        "tdesign_final_mm": tdesign_final,
        "lmin_transfer_mm": lmin_transfer,
        "installation_temp_c": installation_temp_c,
        "component_type": component_type,
        "cyclic_derating_factor": cyclic_derating_factor,
        "axial_load_case": axial_load_case,
    }


def _validate_inputs(
    od,
    wall,
    pressure,
    temp,
    length,
    rem_wall,
    yield_strength,
    design_factor,
    design_life,
    allow_unqualified_temperature=False,
):
    errors = []
    if od <= 0:
        errors.append("Pipe outer diameter must be greater than zero.")
    if wall <= 0:
        errors.append("Nominal wall thickness must be greater than zero.")
    if pressure < 0:
        errors.append("Design pressure cannot be negative.")
    if temp > PROWRAP["max_temp"] and not allow_unqualified_temperature:
        errors.append(
            f"Operating temperature ({temp} degC) exceeds Prowrap limit of "
            f"{PROWRAP['max_temp']} degC."
        )
    if length <= 0:
        errors.append("Defect length must be greater than zero.")
    if rem_wall < 0:
        errors.append("Remaining wall thickness cannot be negative.")
    if rem_wall > wall:
        errors.append(
            "Remaining wall thickness cannot be greater than nominal wall thickness."
        )
    if yield_strength <= 0:
        errors.append("Pipe yield strength must be greater than zero.")
    if not 0 < design_factor <= 1:
        errors.append("Design factor must be greater than zero and less than or equal to 1.")
    if design_life < 1:
        errors.append("Design life must be at least 1 year.")

    if errors:
        raise ValueError("\n".join(errors))


def _selected_cloth_widths(cloth_widths_mm, cloth_width_mm):
    """Return the two selected widths, preserving the engine's single-width API."""
    if cloth_widths_mm is not None:
        if cloth_width_mm is not None:
            raise ValueError("Supply either cloth_widths_mm or cloth_width_mm, not both.")
        return cloth_widths_mm
    if cloth_width_mm is None:
        cloth_width_mm = PROWRAP["cloth_width_mm"]
    return (cloth_width_mm, cloth_width_mm)


def iso_type_b_min_thickness(
    pressure_mpa,
    od_mm,
    nominal_wall_mm,
    defect_size_mm,
    design_temp_c,
    design_life_years,
):
    """ISO 24817 Formula (12) - minimum laminate thickness for a circular or
    near-circular through-wall (Type B) defect.

    p = fT2 * fleak * sqrt(0.001 * gamma_LCL / X)
    X = ((1 - nu^2)/E_ac) * (3*d^4/(512*t^3) + d/pi) + 3*d^2/(64*G*t)

    with E_ac = sqrt(Ea*Ec), fleak per Formula (16) Class 3 and gamma_LCL
    from the PRW110 Annex D qualification. Solved for the smallest t whose
    allowable pressure reaches the design pressure.

    Returns (t_min_mm, details_dict).
    """
    gamma_lcl = PROWRAP["gamma_lcl"]
    e_ac = math.sqrt(PROWRAP["modulus_axial"] * PROWRAP["modulus_circ"])
    g = PROWRAP["shear_modulus"]
    nu = PROWRAP["poisson_circ"]

    # Defect size at end of design life; never less than 15 mm (7.5.7).
    d = max(defect_size_mm, 15.0)

    # Formula (16), Class 3 service factor.
    fleak = 0.666 * 10 ** (-0.01584 * (design_life_years - 1.0))
    # Upper service temperature limit (Table 6): Class 3 Type B repairs with
    # lifetime > 2 years are limited to Tg - 30 (stricter than the Tg - 20
    # Type A limit).
    if design_life_years > 2:
        tm_type_b = PROWRAP["glass_transition_temp"] - 30.0
    else:
        tm_type_b = PROWRAP["max_temp"]
    # Table 8 polynomial; Ttest == Tamb in the PRW110 qualification.
    ft2_delta = tm_type_b - design_temp_c
    ft2 = 0.0000625 * ft2_delta**2 + 0.00125 * ft2_delta + 0.7

    def allowable_pressure(t):
        x = ((1.0 - nu * nu) / e_ac) * (
            3.0 * d**4 / (512.0 * t**3) + d / math.pi
        ) + 3.0 * d * d / (64.0 * g * t)
        return ft2 * fleak * math.sqrt(0.001 * gamma_lcl / x)

    # Asymptotic limit: as t -> infinity, X -> ((1-nu^2)/E_ac)*(d/pi), so
    # there is a maximum achievable pressure regardless of thickness.
    x_asymptote = ((1.0 - nu * nu) / e_ac) * (d / math.pi)
    p_max_asymptote = ft2 * fleak * math.sqrt(0.001 * gamma_lcl / x_asymptote)

    # Formula (12) validity: d <= 6*sqrt(D*t_substrate).
    d_validity_limit = 6.0 * math.sqrt(od_mm * nominal_wall_mm)
    details = {
        "defect_size_used_mm": d,
        "design_life_years": design_life_years,
        "service_temp_limit_c": tm_type_b,
        "fleak": fleak,
        "ft2": ft2,
        "gamma_lcl_j_m2": gamma_lcl,
        "e_ac_mpa": e_ac,
        "p_max_asymptote_mpa": p_max_asymptote,
        "d_validity_limit_mm": d_validity_limit,
        "d_within_validity": d <= d_validity_limit,
    }

    if pressure_mpa >= 0.999 * p_max_asymptote:
        details["repairable_formula12"] = False
        return None, details
    details["repairable_formula12"] = True

    lower, upper = 0.01, 1.0
    while allowable_pressure(upper) < pressure_mpa:
        upper *= 2.0
    for _ in range(200):
        mid = 0.5 * (lower + upper)
        if allowable_pressure(mid) < pressure_mpa:
            lower = mid
        else:
            upper = mid
    return upper, details


def calculate_repair(
    customer,
    location,
    report_no,
    od,
    wall,
    pressure,
    temp,
    defect_type,
    defect_loc,
    length,
    rem_wall,
    yield_strength,
    design_factor,
    design_life,
    force_3_layers=False,
    internal_corrosion_rate=0.0,
    installation_temp=20.0,
    component_type="Straight",
    cyclic_derating_factor=1.0,
    axial_load_case=0,
    cloth_widths_mm=None,
    cloth_width_mm=None,
    allow_unqualified_temperature=False,
    defect_length_basis=ACTUAL_DEFECT_LENGTH,
    individual_defects=(),
):
    """Calculate repair outputs (baseline route).

    internal_corrosion_rate (mm/yr): post-repair growth of INTERNAL
    corrosion, used to project the remaining wall to end of design life.
    External Type A defects are sealed by the repair (rate = 0).

    Routing: External corrosion and canonical dent defects with at least
    1 mm remaining wall follow the Type A route. Dent-with-crack receives
    no substrate credit; dent-without-crack uses the approved component-pipe
    allowable basis. Internal defects, cracks/leaks, and defects below 1 mm
    remaining wall follow the Type B route (through-wall formulas, no credit).

    installation_temp (degC): repair installation temperature, used in the
    ISO 24817 Formula (10) thermal-mismatch strain term.
    component_type: Straight, Bend, Tee, Flange or Reducer (Table 12 f_th).
    cyclic_derating_factor: ISO 24817 Formula (25) factor fc (0 < fc <= 1).
    axial_load_case: 0 = buried restrained pipeline (no axial load);
    1 = severed-pipe/guillotine credible or above-ground pipeline
    (Formula 4 pressure end-thrust).
    """
    allowed_axial_cases = {0, 1}
    _validate_inputs(
        od,
        wall,
        pressure,
        temp,
        length,
        rem_wall,
        yield_strength,
        design_factor,
        design_life,
        allow_unqualified_temperature=allow_unqualified_temperature,
    )
    defect_type = normalize_mechanism(defect_type)
    defect_loc = "" if defect_loc is None else str(defect_loc).strip()
    if defect_loc not in {"External", "Internal"}:
        raise ValueError(
            f"Unsupported defect location: {defect_loc or '(blank)'}"
        )
    if axial_load_case not in allowed_axial_cases:
        raise ValueError(f"Unsupported axial load case: {axial_load_case}")
    if internal_corrosion_rate < 0:
        raise ValueError("Internal corrosion rate cannot be negative.")
    if not 0 < cyclic_derating_factor <= 1:
        raise ValueError(
            "Cyclic derating factor must be greater than zero and less than "
            "or equal to 1."
        )
    baseline_component_factor(component_type)  # validates component type
    stitching_overlap_mm = PROWRAP["stitching_overlap_mm"]
    cloth_widths_mm = _selected_cloth_widths(cloth_widths_mm, cloth_width_mm)

    applied_basis = ACTUAL_DEFECT_LENGTH
    repair_zone_length_mm = length
    interaction_distance_mm = 3.0 * wall
    defect_basis_assumptions = ()
    corrosion_plan = None
    assessment_remaining_wall = rem_wall
    if defect_type == "Corrosion" and defect_loc == "External":
        corrosion_plan = build_corrosion_assessment_plan(
            basis=defect_length_basis,
            repair_zone_length_mm=length,
            nominal_wall_mm=wall,
            default_remaining_wall_mm=rem_wall,
            manual_defects=tuple(individual_defects),
        )
        applied_basis = corrosion_plan.basis
        repair_zone_length_mm = corrosion_plan.repair_zone_length_mm
        interaction_distance_mm = corrosion_plan.interaction_distance_mm
        defect_basis_assumptions = corrosion_plan.assumptions
        assessment_remaining_wall = corrosion_plan.minimum_remaining_wall_mm

    wall_loss_ratio = (wall - assessment_remaining_wall) / wall

    # Remaining wall projected to END of repair design life (ISO 24817 7.3):
    # external corrosion is sealed by the repair (rate 0); internal
    # corrosion keeps growing under the laminate at the given rate.
    if defect_type == "Corrosion" and defect_loc == "Internal":
        rem_wall_eol = max(rem_wall - internal_corrosion_rate * design_life, 0.0)
    elif defect_type == "Corrosion" and defect_loc == "External":
        rem_wall_eol = assessment_remaining_wall
    else:
        rem_wall_eol = rem_wall
    has_no_substrate_capacity = rem_wall_eol < 1.0

    # Routing: eligible external corrosion and either canonical dent follow
    # Type A. Internal defects, cracks, leaks, and defects below 1 mm follow
    # Type B without substrate credit.
    is_type_b = (
        defect_loc == "Internal"
        or defect_type in ["Leak", "Crack"]
        or has_no_substrate_capacity
    )
    if is_type_b:
        calc_method_thick = "Type B (Total Replacement)"
        calc_method_overlap = "Type B (Shear Controlled)"
    elif defect_type in {DENT_WITH_CRACK, DENT_NO_CRACK}:
        calc_method_thick = "Type A (Dent Reinforcement)"
        calc_method_overlap = "Type A (Geometry Controlled)"
    else:
        calc_method_thick = "Type A (Load Sharing)"
        calc_method_overlap = "Type A (Geometry Controlled)"

    if is_type_b:
        calculation_basis = "Type B full replacement"
    elif defect_type == DENT_WITH_CRACK:
        calculation_basis = "Dent w/crack - full-pressure laminate"
    elif defect_type == DENT_NO_CRACK:
        calculation_basis = "Dent no-crack - substrate load sharing"
    else:
        calculation_basis = "ASME B31G-2023 Level 1 (Modified)"

    safety_factor = 1.0 / design_factor

    # ISO 24817 allowable strain, 7.5.6 performance route (Formula 11):
    # eps_c = fc * fperf * fT2 * eps_lt, with Class 3 design-life-data fperf
    # (Table 10), the Table 8 polynomial for fT2 (Ttest == Tamb in the
    # PRW110 qualification, so the argument reduces to Tm - Td) and the
    # Formula (25) cyclic derating factor fc.
    eps_lt = PROWRAP.get("long_term_strain_lcl", PROWRAP.get("long_term_strain_20y"))
    fperf = 0.76 * 10 ** (-0.00273 * design_life)
    ft2_delta = PROWRAP["max_temp"] - temp
    temp_factor = 0.0000625 * ft2_delta**2 + 0.00125 * ft2_delta + 0.7
    design_strain = cyclic_derating_factor * fperf * temp_factor * eps_lt

    pressure_mpa = pressure * 0.1

    # Substrate MAWP (p_s) from an ASME B31G-2023 Level 1 (Modified)
    # defect assessment, as ISO 24817 requires. B31G covers blunt metal
    # loss only; the assessment is run for corrosion defects for
    # information, but PRESSURE CREDIT is only taken on the Type A route
    # (external corrosion sealed by the repair). Type B (internal, crack,
    # leak, < 1 mm projected wall) takes no substrate credit.
    b31g_details = None
    b31g_assessments = []
    governing_id = None
    governing_length = None
    governing_wall = None
    p_steel_capacity = 0.0
    allowable_pipe_stress_mpa = None
    if corrosion_plan is not None:
        for defect in corrosion_plan.candidates:
            assessment = assess_b31g(
                od_mm=od,
                wall_mm=wall,
                depth_mm=wall - defect.remaining_wall_mm,
                length_mm=defect.longitudinal_length_mm,
                smys_mpa=yield_strength,
                safety_factor=max(1.0 / design_factor, 1.25),
                method="modified",
                operating_pressure_mpa=pressure_mpa,
            )
            credited_pressure = (
                assessment["p_s_mpa"]
                if assessment["applicable"] and defect.remaining_wall_mm >= 1.0
                else 0.0
            )
            b31g_assessments.append(
                {
                    "defect_id": defect.defect_id,
                    "length_mm": defect.longitudinal_length_mm,
                    "remaining_wall_mm": defect.remaining_wall_mm,
                    "credited_pressure_mpa": credited_pressure,
                    "assessment": assessment,
                }
            )

        governing = min(
            b31g_assessments,
            key=lambda item: item["credited_pressure_mpa"],
        )
        governing_id = governing["defect_id"]
        governing_length = governing["length_mm"]
        governing_wall = governing["remaining_wall_mm"]
        b31g_details = governing["assessment"]
        if "Type A" in calc_method_thick:
            p_steel_capacity = governing["credited_pressure_mpa"]
    elif defect_type == "Corrosion" and not has_no_substrate_capacity:
        # Depth is taken at END of design life (internal corrosion
        # projected at the given rate; external sealed by the repair).
        b31g_details = assess_b31g(
            od_mm=od,
            wall_mm=wall,
            depth_mm=wall - rem_wall_eol,
            length_mm=length,
            smys_mpa=yield_strength,
            safety_factor=max(1.0 / design_factor, 1.25),
            method="modified",
            operating_pressure_mpa=pressure_mpa,
        )
        # d/t > 0.80: beyond B31G - no Level 1 substrate credit.
        if "Type A" in calc_method_thick and b31g_details["applicable"]:
            p_steel_capacity = b31g_details["p_s_mpa"]
    elif defect_type == DENT_NO_CRACK and not is_type_b:
        pipe_basis = component_pipe_allowable_basis(
            od_mm=od,
            remaining_wall_mm=rem_wall,
            smys_mpa=yield_strength,
            design_factor=design_factor,
        )
        allowable_pipe_stress_mpa = pipe_basis["allowable_stress_mpa"]
        p_steel_capacity = pipe_basis["allowable_pressure_mpa"]

    if (
        b31g_details is not None
        and calculation_basis.startswith("ASME B31G")
    ):
        method_label = b31g_details["method"].title()
        applicability_label = (
            "" if b31g_details["applicable"] else "; outside applicability"
        )
        calculation_basis = (
            "ASME B31G-2023 Level 1 "
            f"({method_label}{applicability_label})"
        )

    if "Type A" in calc_method_thick and p_steel_capacity > 0:
        p_composite_design = max(0, pressure_mpa - p_steel_capacity)
    else:
        p_composite_design = pressure_mpa

    # Thickness:
    # - Type A route: full ISO 24817 Type A design (Formulae 4/5/10/11/25,
    #   Table 12 f_th, Formula 33 tee cap, 7.5.14 floor).
    # - Type B route: hoop Type A equation at full pressure (the 7.5.7
    #   cross-check), combined below with Formula (12).
    typea_design = None
    if "Type A" in calc_method_thick:
        typea_design = baseline_type_a_design(
            od_mm=od,
            nominal_wall_mm=wall,
            pressure_mpa=pressure_mpa,
            substrate_pressure_mpa=p_steel_capacity,
            design_temp_c=temp,
            installation_temp_c=installation_temp,
            design_life_years=design_life,
            component_type=component_type,
            cyclic_derating_factor=cyclic_derating_factor,
            axial_load_case=axial_load_case,
        )
        t_required = typea_design["tdesign_final_mm"]
    elif p_composite_design > 0:
        t_required = (
            p_composite_design * od
        ) / (2 * PROWRAP["modulus_circ"] * design_strain)
    else:
        t_required = 0.0

    # Type B (through-wall) designs must satisfy BOTH the Formula (12)
    # energy-release-rate equation and the Type A equations (7.5.7):
    # take the maximum thickness.
    type_b_details = None
    if "Type B" in calc_method_thick and pressure_mpa > 0:
        # Type B service life is capped at 2 years for PRW110; the repair
        # must be revalidated or replaced beyond that.
        type_b_life = min(design_life, PROWRAP["type_b_max_life_years"])
        t_type_b, type_b_details = iso_type_b_min_thickness(
            pressure_mpa=pressure_mpa,
            od_mm=od,
            nominal_wall_mm=wall,
            defect_size_mm=length,
            design_temp_c=temp,
            design_life_years=type_b_life,
        )
        type_b_details["t_formula12_mm"] = t_type_b
        type_b_details["t_typea_mm"] = t_required
        if t_type_b is not None:
            t_required = max(t_required, t_type_b)

    num_plies = math.ceil(t_required / PROWRAP["ply_thickness"])
    # ISO 24817 7.5.14: Type A minimum is the greater of 2 layers or 2 mm
    # (3 plies at 0.83 mm/ply). Type B minimum is the Annex F
    # impact-qualified layer count (3 layers for PRW110).
    min_plies_iso = math.ceil(2.0 / PROWRAP["ply_thickness"])
    if "Type B" in calc_method_thick:
        min_plies = max(PROWRAP["type_b_min_layers"], min_plies_iso)
    else:
        min_plies = min_plies_iso
    num_plies = max(num_plies, min_plies)

    is_upgraded = False
    if force_3_layers and num_plies < 3:
        num_plies = 3
        is_upgraded = True

    final_thickness = num_plies * PROWRAP["ply_thickness"]

    # ISO 24817 7.5.8 axial extent:
    # Formula (18) geometric overlap 2*sqrt(D*t), never less than 50 mm,
    # plus the Formula (21) load-transfer check 3*Ea*eps_a*t/tau.
    overlap_geometric = 2.0 * math.sqrt(od * wall)
    if typea_design is not None:
        # Formula (21) on the base (pre-f_th) thickness with the axial
        # allowable strain eps_a (thermal mismatch + cyclic included).
        overlap_transfer = typea_design["lmin_transfer_mm"]
        overlap_shear_basis = "iso_formula_18_and_21"
        overlap_shear_strength = PROWRAP["long_term_lap_shear"]
    else:
        overlap_transfer = (
            3.0 * PROWRAP["modulus_axial"] * design_strain * final_thickness
        ) / PROWRAP["long_term_lap_shear"]
        overlap_shear_basis = "iso_formula_18_and_21_type_b"
        overlap_shear_strength = PROWRAP["long_term_lap_shear"]
    overlap_length = max(50.0, overlap_geometric, overlap_transfer)

    # Formula (20): total length = defect + 2*overlap + 2*taper (taper >= 5:1).
    taper_length = 5.0 * final_thickness
    total_repair_length_calc = length + (2 * overlap_length) + (2 * taper_length)

    band_procurement = optimize_band_procurement(
        total_repair_length_calc, cloth_widths_mm, stitching_overlap_mm
    )
    normalized_cloth_widths_mm = tuple(sorted(float(width) for width in cloth_widths_mm))
    procurement_axial_length = band_procurement.procurement_axial_length_mm

    circumference_m = (math.pi * od) / 1000
    axial_procurement_m = procurement_axial_length / 1000
    optimized_sqm = axial_procurement_m * circumference_m * num_plies
    epoxy_kg = optimized_sqm * 1.2

    compliance_warnings = []
    if temp > PROWRAP["max_temp"]:
        compliance_warnings.append(
            f"Design temperature {temp:.1f} degC exceeds the qualified "
            f"Prowrap limit of {PROWRAP['max_temp']:.2f} degC. The result "
            "requires engineering review before repair design or installation."
        )
    if (
        type_b_details is not None
        and not type_b_details.get("repairable_formula12", True)
    ):
        compliance_warnings.append(
            "NOT REPAIRABLE PER ISO 24817 FORMULA 12: the maximum achievable "
            f"pressure for a {type_b_details['defect_size_used_mm']:.0f} mm "
            "through-wall defect with PRW110 (gamma_LCL = "
            f"{type_b_details['gamma_lcl_j_m2']:.0f} J/m2) is "
            f"{type_b_details['p_max_asymptote_mpa']:.2f} MPa, below the "
            f"design pressure of {pressure_mpa:.2f} MPa. No laminate "
            "thickness can satisfy Formula 12 - do not install this repair; "
            "reduce pressure, reduce the defect size, or use another method."
        )
    if "Type B" in calc_method_thick:
        if design_life > PROWRAP["type_b_max_life_years"]:
            compliance_warnings.append(
                "Type B service life is capped at "
                f"{PROWRAP['type_b_max_life_years']:.0f} years for PRW110 "
                f"(requested: {design_life:.0f}). The repair must be "
                "inspected and revalidated or replaced at the end of the "
                "Type B service life."
            )
    if "Type B" in calc_method_thick and type_b_details is not None:
        if temp > type_b_details["service_temp_limit_c"]:
            compliance_warnings.append(
                f"Design temperature {temp:.1f} degC exceeds the Type B "
                "upper service limit of "
                f"{type_b_details['service_temp_limit_c']:.1f} degC "
                "(Tg - 30 for Class 3 Type B repairs over 2 years). "
                "This repair is outside the qualified temperature range."
            )
    if "Type B" in calc_method_thick:
        if type_b_details is None:
            compliance_warnings.append(
                "Type B defect at zero design pressure: Formula 12 is "
                "non-controlling; the impact-qualified three-ply minimum is "
                "shown and engineering review of the Type B defect "
                "classification is required."
            )
        else:
            compliance_warnings.append(
                "Type B design assumes a circular/near-circular defect of size "
                f"{type_b_details['defect_size_used_mm']:.0f} mm at END of the "
                "design life (defect growth must be projected by the assessor). "
                "Annex F impact-qualified minimum of "
                f"{PROWRAP['type_b_min_layers']} layers applied."
            )
        if type_b_details is not None and not type_b_details["d_within_validity"]:
            compliance_warnings.append(
                "Formula 12 validity exceeded: defect size "
                f"{type_b_details['defect_size_used_mm']:.0f} mm > "
                f"6*sqrt(D*t) = {type_b_details['d_validity_limit_mm']:.0f} mm. "
                "The Type B result is outside the validated range - an "
                "engineered assessment is required."
            )
    if b31g_assessments:
        for item in b31g_assessments:
            defect_prefix = f"Defect ID {item['defect_id']}: "
            assessment = item["assessment"]
            compliance_warnings.extend(
                f"{defect_prefix}B31G: {warning}"
                for warning in assessment["warnings"]
            )
            if item["remaining_wall_mm"] < 1.0:
                compliance_warnings.append(
                    f"{defect_prefix}remaining wall is below 1 mm; no "
                    "substrate pressure credit is taken."
                )
            if assessment["applicable"] and not assessment["acceptable"]:
                compliance_warnings.append(
                    f"{defect_prefix}B31G Level 1: the corroded pipe alone "
                    "is NOT acceptable at the design pressure "
                    f"(safe pressure P_S = {assessment['p_s_mpa']:.2f} MPa < "
                    f"{pressure_mpa:.2f} MPa) - the composite repair is "
                    "structural, not just preventive."
                )
    elif b31g_details is not None:
        compliance_warnings.extend(
            f"B31G: {w}" for w in b31g_details["warnings"]
        )
        if b31g_details["applicable"] and not b31g_details["acceptable"]:
            compliance_warnings.append(
                "B31G Level 1: the corroded pipe alone is NOT acceptable at "
                "the design pressure "
                f"(safe pressure P_S = {b31g_details['p_s_mpa']:.2f} MPa < "
                f"{pressure_mpa:.2f} MPa) - the composite repair is "
                "structural, not just preventive."
            )
        # End-of-life defect size: external Type A corrosion is sealed by
        # the repair (post-repair rate 0, current wall = end-of-life wall);
        # internal corrosion is projected forward at internal_corrosion_rate.
    if defect_type == "Corrosion" and defect_loc == "Internal":
        if internal_corrosion_rate > 0:
            compliance_warnings.append(
                "Internal corrosion projected at "
                f"{internal_corrosion_rate:.2f} mm/yr: remaining wall "
                f"{rem_wall:.2f} mm now -> {rem_wall_eol:.2f} mm at end of "
                f"the {design_life:.0f}-year design life. Assessment and "
                "classification use the end-of-life wall."
            )
        else:
            compliance_warnings.append(
                "Internal corrosion with corrosion rate = 0 mm/yr: the "
                "defect remains exposed to the process fluid under the "
                "repair. Enter a corrosion rate so the remaining wall can "
                "be projected to the end of the design life (ISO 24817 7.3)."
            )
    if is_type_b and axial_load_case == 1:
        compliance_warnings.append(
            "Axial load case 1 (Formula 4 end-thrust) selected with a Type B "
            "defect: the Formula 12 through-wall design does not include "
            "axial loads. An engineered assessment of the axial load path "
            "is required for severed-pipe / above-ground Type B repairs."
        )
    thickness_check_ok = final_thickness < od / 12.0
    if not thickness_check_ok:
        compliance_warnings.append(
            "Repair thickness exceeds D/12: the thin-wall design formulae "
            "of ISO 24817 are not valid for this repair."
        )
    compliance_warnings = list(dict.fromkeys(compliance_warnings))

    return {
        "customer": customer,
        "location": location,
        "report_no": report_no,
        "od": od,
        "wall": wall,
        "yield_str": yield_strength,
        "pressure": pressure,
        "temp": temp,
        "defect_type": defect_type,
        "defect_loc": defect_loc,
        "rem_wall": rem_wall,
        "rem_wall_eol": rem_wall_eol,
        "internal_corrosion_rate": internal_corrosion_rate,
        "length": length,
        "wall_loss_ratio": wall_loss_ratio,
        "has_no_substrate_capacity": has_no_substrate_capacity,
        "is_severe_loss": has_no_substrate_capacity,
        "calc_method_thick": calc_method_thick,
        "calc_method_overlap": calc_method_overlap,
        "calculation_basis": calculation_basis,
        "allowable_pipe_stress_mpa": allowable_pipe_stress_mpa,
        "safety_factor": safety_factor,
        "temp_factor": temp_factor,
        "design_strain": design_strain,
        "pressure_mpa": pressure_mpa,
        "p_steel_capacity": p_steel_capacity,
        "p_composite_design": p_composite_design,
        "t_required": t_required,
        "num_plies": num_plies,
        "final_thickness": final_thickness,
        "iso_length": total_repair_length_calc,
        "overlap_length": overlap_length,
        "overlap_geometric": overlap_geometric,
        "overlap_transfer": overlap_transfer,
        "taper_length": taper_length,
        "overlap_shear_basis": overlap_shear_basis,
        "overlap_shear_strength": overlap_shear_strength,
        "eps_lt": eps_lt,
        "fperf": fperf,
        "installation_temp": installation_temp,
        "component_type": component_type,
        "cyclic_derating_factor": cyclic_derating_factor,
        "axial_load_case": axial_load_case,
        "typea_design": typea_design,
        "type_b_details": type_b_details,
        "b31g_details": b31g_details,
        "defect_length_basis": applied_basis,
        "repair_zone_length_mm": repair_zone_length_mm,
        "interaction_distance_mm": interaction_distance_mm,
        "defect_basis_assumptions": defect_basis_assumptions,
        "b31g_assessments": tuple(b31g_assessments),
        "governing_defect_id": governing_id,
        "governing_b31g_length_mm": governing_length,
        "governing_b31g_remaining_wall_mm": governing_wall,
        "thickness_check_ok": thickness_check_ok,
        "compliance_warnings": compliance_warnings,
        "num_bands_500": band_procurement.count_500,
        "num_bands_300": band_procurement.count_300,
        "num_bands": band_procurement.total_band_count,
        "proc_length": procurement_axial_length,
        "covered_length_mm": band_procurement.covered_length_mm,
        "excess_coverage_mm": band_procurement.excess_coverage_mm,
        "sf": safety_factor,
        "design_factor": design_factor,
        "design_life": design_life,
        "cloth_widths_mm": normalized_cloth_widths_mm,
        "cloth_width_mm": (
            normalized_cloth_widths_mm[0]
            if normalized_cloth_widths_mm[0] == normalized_cloth_widths_mm[1]
            else None
        ),
        "optimized_sqm": optimized_sqm,
        "epoxy_kg": epoxy_kg,
        "is_upgraded": is_upgraded,
    }


def calculate_type_a_class3_prowrap_check(
    od,
    pressure_bar,
    temp,
    rem_wall,
    design_life,
    substrate_allowable_pressure_bar=0.0,
    installation_temp=20.0,
    component_type="Straight",
    cyclic_derating_factor=1.0,
    nominal_wall_mm=None,
    axial_load_case=0,
):
    """Run the isolated ISO Type A/Class 3 route using PRW110 performance data.

    axial_load_case:
      0 - buried restrained pipeline: no axial load on the laminate
          (pressure end-thrust carried by pipe wall and soil restraint).
      1 - severed-pipe/guillotine credible, or above-ground pipeline near
          bends/closures: axial loads calculated per ISO Formula 4
          (pressure end-thrust pi/4 * p * D^2).

    Uses the ISO 24817 7.5.6 performance route (Formula 11,
    eps_c = fperf * fT2 * eps_lt) when PRW110 long-term strain LCL data is
    present in the material dataset; otherwise falls back to Table 9 strains.
    """
    eps_lt = PROWRAP.get("long_term_strain_lcl", PROWRAP.get("long_term_strain_20y"))
    inputs = TypeAClass3Inputs(
        pressure_mpa=pressure_bar * 0.1,
        substrate_allowable_pressure_mpa=substrate_allowable_pressure_bar * 0.1,
        outside_diameter_mm=od,
        remaining_wall_mm=rem_wall,
        design_life_years=design_life,
        design_temperature_c=temp,
        installation_temperature_c=installation_temp,
        max_repair_temperature_c=PROWRAP["max_temp"],
        ambient_test_temperature_c=20.0,
        qualification_test_temperature_c=20.0,
        hoop_modulus_mpa=PROWRAP["modulus_circ"],
        axial_modulus_mpa=PROWRAP["modulus_axial"],
        poisson_ratio=PROWRAP["poisson_circ"],
        hoop_cte_per_c=PROWRAP["thermal_expansion_circ"] * 1e-6,
        axial_cte_per_c=PROWRAP["thermal_expansion_axial"] * 1e-6,
        lap_shear_mpa=PROWRAP["long_term_lap_shear"],
        layer_thickness_mm=PROWRAP["ply_thickness"],
        use_performance_data=eps_lt is not None,
        long_term_strain_lcl=eps_lt,
        performance_data_source="Design life",
        # None lets the module compute the ISO Formula 4 end-thrust.
        equivalent_axial_load_n=None if axial_load_case == 1 else 0.0,
        cyclic_derating_factor=cyclic_derating_factor,
        component_type=component_type,
        nominal_wall_mm=nominal_wall_mm,
    )
    result = calculate_type_a_class3(inputs)
    result["input_summary"] = {
        "pressure_bar": pressure_bar,
        "remaining_wall_mm": rem_wall,
        "substrate_allowable_pressure_bar": substrate_allowable_pressure_bar,
        "hoop_modulus_mpa": PROWRAP["modulus_circ"],
        "axial_modulus_mpa": PROWRAP["modulus_axial"],
        "lap_shear_mpa": PROWRAP["long_term_lap_shear"],
        "long_term_strain_lcl": eps_lt,
        "performance_data": (
            f"Formula 11 performance route, eps_lt={eps_lt} (design-life data)"
            if eps_lt is not None
            else "not used - Table 9 fallback"
        ),
    }
    return result


calculate_type_a_class3_fallback_check = calculate_type_a_class3_prowrap_check


def substrate_credit_bar_for_iso_check(repair_data):
    """Return the substrate pressure credit for ISO checks in bar.

    p_steel_capacity already encodes the substrate-credit scope rules:
    B31G for eligible external corrosion, approved component-pipe pressure
    for eligible external dent without crack, and no credit for cracks,
    leaks, dent with crack, internal defects, or < 1 mm remaining wall.
    """
    if repair_data["defect_type"] in {"Crack", "Leak"}:
        return 0.0
    return max(0.0, repair_data["p_steel_capacity"] * 10.0)


def apply_type_a_class3_result_to_repair(
    repair_data,
    typea_class3_result,
    cloth_width_mm=None,
    cloth_widths_mm=None,
):
    """Use the ISO Type A/Class 3 result as the controlling displayed repair design."""
    updated = dict(repair_data)
    updated["iso_typea_class3"] = typea_class3_result
    if updated["p_composite_design"] <= 0:
        updated["iso_typea_class3_controls"] = False
        updated["iso_typea_class3_noncontrolling_reason"] = (
            "effective_pipe_capacity_covers_design_pressure"
        )
        return updated

    updated["iso_typea_class3_controls"] = True
    updated["iso_typea_class3_noncontrolling_reason"] = None
    layer_count = typea_class3_result["layer_count"]
    final_installed_thickness = layer_count * PROWRAP["ply_thickness"]
    overlap_length = typea_class3_result["lover_required_mm"]
    taper_length = typea_class3_result.get("taper_length_mm", 0.0)
    # Formula (20): total length = defect + 2*overlap + 2*taper.
    repair_length = updated["length"] + (2.0 * overlap_length) + (2.0 * taper_length)

    if cloth_widths_mm is None and cloth_width_mm is None:
        cloth_widths_mm = updated.get("cloth_widths_mm")
    cloth_widths_mm = _selected_cloth_widths(cloth_widths_mm, cloth_width_mm)
    band_procurement = optimize_band_procurement(
        repair_length, cloth_widths_mm, PROWRAP["stitching_overlap_mm"]
    )
    normalized_cloth_widths_mm = tuple(sorted(float(width) for width in cloth_widths_mm))
    procurement_axial_length = band_procurement.procurement_axial_length_mm

    circumference_m = (math.pi * updated["od"]) / 1000.0
    axial_procurement_m = procurement_axial_length / 1000.0
    optimized_sqm = axial_procurement_m * circumference_m * layer_count

    updated.update(
        {
            "calc_method_thick": "ISO 24817 Type A / Class 3",
            "calc_method_overlap": "ISO 24817 Formula 21",
            "t_required": typea_class3_result["tdesign_final_mm"],
            "num_plies": layer_count,
            "final_thickness": final_installed_thickness,
            "iso_length": repair_length,
            "overlap_length": overlap_length,
            "taper_length": taper_length,
            "overlap_shear_basis": "iso_formula_18_and_21",
            "overlap_shear_strength": PROWRAP["long_term_lap_shear"],
            "num_bands_500": band_procurement.count_500,
            "num_bands_300": band_procurement.count_300,
            "num_bands": band_procurement.total_band_count,
            "proc_length": procurement_axial_length,
            "covered_length_mm": band_procurement.covered_length_mm,
            "excess_coverage_mm": band_procurement.excess_coverage_mm,
            "optimized_sqm": optimized_sqm,
            "epoxy_kg": optimized_sqm * 1.2,
            "cloth_widths_mm": normalized_cloth_widths_mm,
            "cloth_width_mm": (
                normalized_cloth_widths_mm[0]
                if normalized_cloth_widths_mm[0] == normalized_cloth_widths_mm[1]
                else None
            ),
            "is_upgraded": False,
        }
    )
    return updated
