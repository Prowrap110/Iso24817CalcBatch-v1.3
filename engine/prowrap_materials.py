"""PROWRAP PRW110 material properties.

Mechanical-property source: PRW110 Test Data.pdf, ISO 24817:2017 and ASME
PCC-2 PROWRAP HPTP repair system qualification data. Tg = 110 degC is a
controlled product-basis override for this release and is not attributed to
the cited PDF; verify it against the controlled product qualification record
before engineering approval.
"""

_GLASS_TRANSITION_TEMP_C = 110.0
APPROVED_CLOTH_WIDTHS_MM = (300.0, 500.0)
STITCHING_OVERLAP_MM = 50.0

PROWRAP = {
    "ply_thickness": 0.83,             # mm, ISO 527-4
    "modulus_circ": 45460,             # MPa, ISO 527-4
    "strain_fail": 0.0233,             # mm/mm, circumferential, ISO 527-4
    "tensile_strength": 574.1,         # MPa, circumferential, ISO 527-4
    "modulus_axial": 43800,            # MPa, ISO 527-4
    "strain_fail_axial": 0.0243,       # mm/mm, axial, ISO 527-4
    "tensile_strength_axial": 563.67,  # MPa, axial, ISO 527-4
    "poisson_circ": 0.066,             # ISO 527-4
    "compressive_modulus": 3310,       # MPa, ISO 604
    "compressive_strength": 85.58,     # MPa, ISO 604
    "shear_modulus": 2450,             # MPa, ASTM D5379
    "shore_d": 79.1,                   # Shore D, measured, ISO 868
    "shore_d_min": 75,                 # Shore D, minimum acceptance for QC
    "glass_transition_temp": _GLASS_TRANSITION_TEMP_C,  # degC, controlled override
    "peak_exotherm_temp": 104,         # degC, ISO 11357-2
    "thermal_expansion_circ": 10.34,   # ppm/K, circumferential, ASTM E831
    "thermal_expansion_axial": 22.81,  # ppm/K, axial, ASTM E831
    "lap_shear": 14.7,                 # MPa, ASTM D3165
    "long_term_lap_shear": 9.62,       # MPa, ASTM D3165
    "long_term_strain_lcl": 0.0055,    # mm/mm (0.55 %), eps_lt, 95% LCL long-term strain,
                                       # ISO 24817 Annex E performance data (Formula 11 route)
    "long_term_strain_20y": 0.0055,    # mm/mm, 0.55% long-term strain at 20 years
                                       # (same value as long_term_strain_lcl, legacy key)
    "gamma_lcl": 250.0,                # J/m^2, energy release rate 95% LCL,
                                       # ISO 24817 Annex D (Type B / Formula 12 route)
    "type_b_min_layers": 3,            # ISO 24817 7.5.14 / Annex F impact-qualified
                                       # minimum layer count for Type B repairs
    "type_b_max_life_years": 2,        # Type B (through-wall) service life cap;
                                       # revalidation required beyond this
    "impact_peak_energy": 41.982,      # J, ASTM D7136
    "short_term_survival": "PASS",     # ISO 24817
    "max_temp": _GLASS_TRANSITION_TEMP_C - 20.0,  # degC, Tg minus 20 design limit
    "cloth_width_mm": APPROVED_CLOTH_WIDTHS_MM[0],
    "stitching_overlap_mm": STITCHING_OVERLAP_MM,
}

PROWRAP_SOURCES = {
    "source_document": "PRW110 Test Data.pdf",
    "controlled_override": (
        "Tg = 110 degC requested for this release on 2026-08-14; verify "
        "against the controlled product qualification record before approval"
    ),
    "qualification_basis": (
        "ISO 24817:2017 and ASME PCC-2 - PROWRAP HPTP repair system "
        "qualification data"
    ),
}
