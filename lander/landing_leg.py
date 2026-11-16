import numpy as np
import config as cfg


class LandingLeg:
    """Модель опоры с линейным демпфером"""

    def __init__(self, attachment_local, rest_length, k, c, max_compression):
        self.attachment_local = np.array(attachment_local)
        self.rest_length = rest_length
        self.k = k
        self.c = c
        self.max_compression = max_compression

        self.force = 0.0
        self.compression = 0.0
        self.velocity = 0.0

    def update(self, dt, foot_position_global, foot_velocity_global):
        """Логика контакта"""
        if foot_position_global[1] <= 0:
            compression = min(abs(foot_position_global[1]), self.max_compression)
            compression_velocity = -foot_velocity_global[1]

            spring_force = self.k * compression
            damping_force = self.c * compression_velocity  # Только линейный
            self.force = max(spring_force + damping_force, 0.0)
            self.compression = compression
            self.velocity = compression_velocity

            return np.array([0.0, self.force])
        else:
            self.force = 0.0
            self.compression = 0.0
            return np.array([0.0, 0.0])

    def get_debug_info(self):
        return {
            'force': self.force,
            'compression': self.compression,
            'contact': self.force > 0
        }