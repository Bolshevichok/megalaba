"""Math models for sensor data generation per research.md R9.

Each model simulates realistic greenhouse sensor readings with
sinusoidal base patterns, noise, and actuator influence.
"""

import math
import random


class TemperatureModel:
    """Temperature sensor simulation model.

    Generates temperature values using sinusoidal diurnal cycle with
    Gaussian noise and actuator effects.

    Formula:
        T(t) = T_base + A * sin(2*pi*t / period) + noise

    Actuator effects per call:
        - heating ON: +0.5
        - ventilation ON: -0.3
    """

    def __init__(self) -> None:
        """Initialize temperature model with default parameters."""
        self.t_base = 24.0
        self.amplitude = 4.0
        self.period = 86400.0  # 24 hours in seconds
        self.sigma = 0.3

    def generate(self, elapsed_seconds: float, actuator_states: dict) -> float:
        """Generate a temperature reading.

        Args:
            elapsed_seconds: Time elapsed since simulator start in seconds.
            actuator_states: Dict of actuator name to state string,
                e.g. {"heating": "on", "ventilation": "off"}.

        Returns:
            Simulated temperature value in degrees Celsius.
        """
        noise = random.gauss(0, self.sigma)
        value = (
            self.t_base
            + self.amplitude * math.sin(2 * math.pi * elapsed_seconds / self.period)
            + noise
        )

        if actuator_states.get("heating") == "on":
            value += 0.5
        if actuator_states.get("ventilation") == "on":
            value -= 0.3

        return round(value, 2)


class HumidityModel:
    """Humidity sensor simulation model.

    Generates humidity values inversely correlated with temperature
    deviation, with Gaussian noise and actuator effects.

    Formula:
        H(t) = H_base - k * (T - T_base) + noise

    Actuator effects per call:
        - watering ON: +5
        - ventilation ON: -2
    """

    def __init__(self) -> None:
        """Initialize humidity model with default parameters."""
        self.h_base = 70.0
        self.k = 2.5
        self.t_base = 24.0
        self.amplitude = 4.0
        self.period = 86400.0
        self.sigma = 1.0

    def generate(self, elapsed_seconds: float, actuator_states: dict) -> float:
        """Generate a humidity reading.

        Args:
            elapsed_seconds: Time elapsed since simulator start in seconds.
            actuator_states: Dict of actuator name to state string,
                e.g. {"watering": "on", "ventilation": "off"}.

        Returns:
            Simulated humidity value in percent.
        """
        temp_deviation = self.amplitude * math.sin(
            2 * math.pi * elapsed_seconds / self.period
        )
        noise = random.gauss(0, self.sigma)
        value = self.h_base - self.k * temp_deviation + noise

        if actuator_states.get("watering") == "on":
            value += 5.0
        if actuator_states.get("ventilation") == "on":
            value -= 2.0

        return round(value, 2)


class LightModel:
    """Light sensor simulation model.

    Generates light intensity values based on solar position with
    Gaussian noise and actuator effects.

    Formula:
        L(t) = L_max * max(0, sin(pi * (hour - sunrise) / daylight)) + noise

    Actuator effects per call:
        - lighting ON: +7500
    """

    def __init__(self) -> None:
        """Initialize light model with default parameters."""
        self.l_max = 50000.0
        self.sunrise = 6.0
        self.daylight = 14.0
        self.sigma = 100.0

    def generate(self, elapsed_seconds: float, actuator_states: dict) -> float:
        """Generate a light intensity reading.

        Args:
            elapsed_seconds: Time elapsed since simulator start in seconds.
            actuator_states: Dict of actuator name to state string,
                e.g. {"lighting": "on"}.

        Returns:
            Simulated light intensity value in lux.
        """
        hour = (elapsed_seconds / 3600.0) % 24.0
        noise = random.gauss(0, self.sigma)
        solar_angle = math.pi * (hour - self.sunrise) / self.daylight
        value = self.l_max * max(0.0, math.sin(solar_angle)) + noise

        if actuator_states.get("lighting") == "on":
            value += 7500.0

        return round(max(0.0, value), 2)
