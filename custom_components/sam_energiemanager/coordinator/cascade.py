"""Modular calculation and cascade logic for sam_energiemanager."""

from dataclasses import dataclass, field
from datetime import datetime
import math
from typing import Any

from custom_components.sam_energiemanager.const import (
    DEADBAND_WATTS,
    EMA_ALPHA,
    EV_MAX_CURRENT_A,
    EV_MIN_CURRENT_A,
    EV_VOLTAGE,
    SESSION_ACTIVE_THRESHOLD_WATTS,
)


def compute_ema(raw_watts: float, prev_ema: float | None, alpha: float = EMA_ALPHA) -> float:
    """
    Calculate the Exponential Moving Average (EMA) of the grid power.

    Returns:
        The smoothed grid power in watts.

    """
    if prev_ema is None:
        return raw_watts
    return alpha * raw_watts + (1.0 - alpha) * prev_ema


def is_within_deadband(filtered_watts: float, deadband: float = DEADBAND_WATTS) -> bool:
    """
    Return whether the filtered grid power lies within the symmetric deadband.

    Returns:
        True if abs(filtered_watts) <= deadband.

    """
    return abs(filtered_watts) <= deadband


def compute_surplus_watts(filtered_watts: float) -> float:
    """
    Compute available PV surplus power from filtered grid power.

    Returns:
        Surplus power in watts (positive when exporting to grid).

    """
    return max(0.0, -filtered_watts)


def compute_ev_target_current(
    surplus_watts: float,
    ev_current_watts: float,
    max_current: int,
) -> int:
    """
    Calculate clamped 1-phase target current in amperes (230 V step size).

    Returns:
        Target current clamped between 6 A and max_current.

    """
    clamped_max = max(EV_MIN_CURRENT_A, min(EV_MAX_CURRENT_A, max_current))
    raw_amps = math.floor((surplus_watts + max(0.0, ev_current_watts)) / EV_VOLTAGE)
    return max(EV_MIN_CURRENT_A, min(clamped_max, raw_amps))


def split_ev_power(ev_watts: float, grid_raw_watts: float) -> tuple[float, float]:
    """
    Split current EV charging power into solar and grid components.

    Returns:
        A tuple of (ev_solar_watts, ev_grid_watts).

    """
    if ev_watts <= 0.0:
        return 0.0, 0.0
    grid_import = max(0.0, grid_raw_watts)
    ev_grid = min(ev_watts, grid_import)
    ev_solar = max(0.0, ev_watts - ev_grid)
    return round(ev_solar, 1), round(ev_grid, 1)


@dataclass
class SessionTracker:
    """WashData-style session tracker and lifetime energy accumulator."""

    solar_lifetime_kwh: float = 0.0
    grid_lifetime_kwh: float = 0.0
    active: bool = False
    start_time: datetime | None = None
    start_soc: float | None = None
    last_known_soc: float | None = None
    session_solar_kwh: float = 0.0
    session_grid_kwh: float = 0.0
    last_summary: str = "No session completed"
    last_session_data: dict[str, Any] = field(default_factory=dict)

    def update(
        self,
        *,
        ev_watts: float,
        grid_raw_watts: float,
        ev_soc: float | None,
        dt_hours: float,
        price_eur_per_kwh: float,
        now_utc: datetime,
    ) -> tuple[float, float, dict[str, Any] | None]:
        """
        Update energy counters and session state for one calculation step.

        Returns:
            Tuple of (ev_solar_watts, ev_grid_watts, completed_session_event_data).

        """
        if ev_soc is not None:
            self.last_known_soc = ev_soc

        ev_solar_w, ev_grid_w = split_ev_power(ev_watts, grid_raw_watts)

        if dt_hours > 0.0 and ev_watts > 0.0:
            d_solar = (ev_solar_w / 1000.0) * dt_hours
            d_grid = (ev_grid_w / 1000.0) * dt_hours
            self.solar_lifetime_kwh = round(self.solar_lifetime_kwh + d_solar, 4)
            self.grid_lifetime_kwh = round(self.grid_lifetime_kwh + d_grid, 4)
            if self.active:
                self.session_solar_kwh += d_solar
                self.session_grid_kwh += d_grid

        is_charging = ev_watts > SESSION_ACTIVE_THRESHOLD_WATTS
        completed_event: dict[str, Any] | None = None

        if is_charging and not self.active:
            self.active = True
            self.start_time = now_utc
            self.start_soc = ev_soc
            self.session_solar_kwh = (ev_solar_w / 1000.0) * max(0.0, dt_hours)
            self.session_grid_kwh = (ev_grid_w / 1000.0) * max(0.0, dt_hours)
        elif not is_charging and self.active:
            total_kwh = round(self.session_solar_kwh + self.session_grid_kwh, 3)
            solar_kwh = round(self.session_solar_kwh, 3)
            grid_kwh = round(self.session_grid_kwh, 3)
            solar_pct = round((solar_kwh / total_kwh) * 100.0, 1) if total_kwh > 0 else 0.0
            grid_pct = round(100.0 - solar_pct, 1) if total_kwh > 0 else 0.0
            duration_min = (
                round((now_utc - self.start_time).total_seconds() / 60.0, 1) if self.start_time is not None else 0.0
            )
            cost_eur = round(grid_kwh * price_eur_per_kwh, 2)

            completed_event = {
                "session_id": now_utc.strftime("%Y-%m-%d_%H-%M-%S"),
                "energy_total_kwh": total_kwh,
                "energy_solar_kwh": solar_kwh,
                "energy_grid_kwh": grid_kwh,
                "solar_percentage": solar_pct,
                "grid_percentage": grid_pct,
                "duration_minutes": duration_min,
                "start_soc": self.start_soc,
                "end_soc": self.last_known_soc,
                "cost_eur": cost_eur,
            }
            self.last_session_data = completed_event
            self.last_summary = f"{total_kwh:.2f} kWh ({solar_pct:.1f}% Solar, {cost_eur:.2f} €)"
            self.active = False
            self.start_time = None

        return ev_solar_w, ev_grid_w, completed_event

