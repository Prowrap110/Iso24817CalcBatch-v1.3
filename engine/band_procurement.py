"""Pure mixed-width PROWRAP cloth-band procurement optimization."""

from dataclasses import dataclass
import math

from prowrap_materials import APPROVED_CLOTH_WIDTHS_MM, STITCHING_OVERLAP_MM


@dataclass(frozen=True)
class BandProcurement:
    count_500: int
    count_300: int
    total_band_count: int
    procurement_axial_length_mm: float
    covered_length_mm: float
    excess_coverage_mm: float


def _finite_number(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number.")

    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number.")
    return number


def _available_widths(cloth_widths_mm: tuple[float, float]) -> tuple[float, ...]:
    if not isinstance(cloth_widths_mm, tuple) or len(cloth_widths_mm) != 2:
        raise ValueError("Exactly two cloth widths must be supplied.")

    widths = tuple(_finite_number(width, "cloth width") for width in cloth_widths_mm)
    unsupported = set(widths).difference(APPROVED_CLOTH_WIDTHS_MM)
    if unsupported:
        raise ValueError("Cloth widths must be approved PROWRAP widths.")
    return tuple(sorted(set(widths)))


def optimize_band_procurement(
    repair_length_mm: float,
    cloth_widths_mm: tuple[float, float],
    overlap_mm: float,
) -> BandProcurement:
    """Return the least-gross feasible 300/500 mm cloth-band plan."""
    repair_length = _finite_number(repair_length_mm, "repair length")
    if repair_length <= 0.0:
        raise ValueError("repair length must be greater than zero.")

    available_widths = _available_widths(cloth_widths_mm)
    overlap = _finite_number(overlap_mm, "overlap")
    if overlap != STITCHING_OVERLAP_MM:
        raise ValueError(f"overlap must equal {STITCHING_OVERLAP_MM} mm.")

    smallest_width = min(available_widths)
    all_smallest_count = max(
        1, math.ceil((repair_length - overlap) / (smallest_width - overlap))
    )
    candidates: list[tuple[tuple[float, int, float, int, int], BandProcurement]] = []

    for total_band_count in range(1, all_smallest_count + 1):
        for count_500 in range(total_band_count + 1):
            count_300 = total_band_count - count_500
            if count_500 and 500.0 not in available_widths:
                continue
            if count_300 and 300.0 not in available_widths:
                continue

            gross = (500.0 * count_500) + (300.0 * count_300)
            covered = gross - (overlap * (total_band_count - 1))
            if covered < repair_length:
                continue

            result = BandProcurement(
                count_500=count_500,
                count_300=count_300,
                total_band_count=total_band_count,
                procurement_axial_length_mm=round(gross, 12),
                covered_length_mm=round(covered, 12),
                excess_coverage_mm=round(covered - repair_length, 12),
            )
            key = (gross, total_band_count, covered - repair_length, -count_500, count_300)
            candidates.append((key, result))

    return min(candidates, key=lambda candidate: candidate[0])[1]
