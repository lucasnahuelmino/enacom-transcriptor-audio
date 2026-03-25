from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class ActivityStateChange:
    timestamp: float
    was_active: bool
    now_active: bool
    peak_level_dbm: float
    reason: str


class ActivityDetector:
    def __init__(
        self,
        threshold_dbm: float,
        hysteresis_db: float,
        min_duration_seconds: float,
        emit_callback: Optional[Callable[[dict], None]] = None,
    ):
        self._threshold_dbm = threshold_dbm
        self._hysteresis_db = hysteresis_db
        self._min_duration_seconds = min_duration_seconds
        self._emit_callback = emit_callback

        self._is_active = False
        self._transition_time = time.time()
        self._state_history = []

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def active_duration_seconds(self) -> float:
        return time.time() - self._transition_time

    @property
    def state_history(self) -> list:
        return list(self._state_history[-30:])

    def update(self, peak_level_dbm: float) -> Optional[ActivityStateChange]:
        is_above_threshold = peak_level_dbm >= self._threshold_dbm
        is_above_release = peak_level_dbm >= (self._threshold_dbm - self._hysteresis_db)

        was_active = self._is_active
        now_active = self._is_active

        if not self._is_active and is_above_threshold:
            now_active = True
            reason = f"Nivel {peak_level_dbm:.1f} dBm > umbral {self._threshold_dbm:.1f} dBm"
        elif self._is_active and not is_above_release:
            now_active = False
            reason = f"Nivel {peak_level_dbm:.1f} dBm < umbral {self._threshold_dbm - self._hysteresis_db:.1f} dBm (histéresis)"
        else:
            return None

        self._is_active = now_active
        now = time.time()
        self._transition_time = now

        change = ActivityStateChange(
            timestamp=now,
            was_active=was_active,
            now_active=now_active,
            peak_level_dbm=peak_level_dbm,
            reason=reason,
        )

        self._state_history.append(
            {
                "timestamp": change.timestamp,
                "was_active": change.was_active,
                "now_active": change.now_active,
                "peak_level_dbm": round(change.peak_level_dbm, 2),
                "reason": change.reason,
            }
        )

        logger.info(
            f"[ActivityDetector] Cambio de estado: {was_active} → {now_active} | {reason}"
        )

        if self._emit_callback:
            self._emit_callback(
                {
                    "was_active": was_active,
                    "now_active": now_active,
                    "peak_level_dbm": round(peak_level_dbm, 2),
                    "reason": reason,
                    "timestamp": now,
                }
            )

        return change

    def update_threshold(self, threshold_dbm: float):
        old = self._threshold_dbm
        self._threshold_dbm = threshold_dbm
        logger.info(f"[ActivityDetector] Umbral actualizado: {old:.1f} → {threshold_dbm:.1f} dBm")

    def update_hysteresis(self, hysteresis_db: float):
        old = self._hysteresis_db
        self._hysteresis_db = hysteresis_db
        logger.info(f"[ActivityDetector] Histéresis actualizada: {old:.1f} → {hysteresis_db:.1f} dB")

    def reset(self):
        self._is_active = False
        self._transition_time = time.time()
        self._state_history.clear()
