import asyncio
import unittest
import aiounittest
from unittest.mock import Mock, MagicMock, patch

from jamz_autopilot.flight.navigation.translation import flight_status


class FlightStatusTest(aiounittest.AsyncTestCase):

    def test_constructor(self):

        status_idle = flight_status(0)
        status_done_command = flight_status(1)
        status_executing_command = flight_status(2)

        self.assertEqual(status_idle.status, 0, "Failed on constructor of flight")
        self.assertEqual(status_done_command.status, 1, "Failed on constructor of flight")
        self.assertEqual(status_executing_command.status, 2, "Failed on constructor of flight")

    def test_equality(self):
        a = flight_status(1)
        b = flight_status(1)
        self.assertEqual(a, b)
        self.assertEqual(b, a)
        self.assertTrue(a == b)
        self.assertTrue(b == a)
        self.assertFalse(a != b)
        self.assertFalse(b != a)
