import asyncio
import unittest
import aiounittest
from unittest.mock import Mock, MagicMock, patch
import time

from jamz_autopilot.flight.navigation.flight_controller import FlightController
from jamz_autopilot.flight.navigation.translation.ardupilot import Ardupilot
from jamz_autopilot.flight.navigation.command import Command



class FlightControllerTest(aiounittest.AsyncTestCase):

    def test_constructor(self):
        controller = FlightController()

        self.assertEqual(controller.commands, [], "Failed to create commands list as part of flight_controller")
        self.assertEqual(controller.current_command, None,
                         "Failed to create current_command as part of flight_controller")
        self.assertEqual(controller.commands, [], "Failed to create commands list as part of flight_controller")
        self.assertEqual(controller.translator, Ardupilot(controller.device), "Failed to create Ardupilot(for "
                                                                              "flight_controller.translator) "
                                                                              "with given device in controller")
        #test that Core.get_instance().on_flight_event(FlightEvent(self)) is called


        # patcher = Mock.mock.patch.object(Ardupilot, '__init__')
        # patched = patcher.start()
        # assert patched.call_count == 1
        # patched.assert_called_with('foo', 'bar')
        # real.something = MagicMock()
        # real.method()
        # real.something.assert_called_once_with(1, 2, 3)

    # @patch('flight_controller.a_fun', return_value=1)
    def test_main_loop(self):
        # involves locks, not sure how to test. Dependent on other things
        # test that asyncio.get_event_loop().call_later(0.5, self.main_loop) is called
        controller = FlightController()
        t0 = time.time()
        controller.command_loop()
        t1 = time.time()
        self.assertGreaterEqual(t1-t0, 0.5, "FlightController.main_loop is not successfully sleeping when its commands array is empty") # not 100% sure of this

        cmd = Command("GOTO", 1, 1)
        controller.commands.append(cmd)

        try:
            controller.command_loop()
            self.assertTrue(controller.operation_lock.locked())
            self.assertEqual(controller.commands, [])
        except Exception as e:
            print(e)

        del controller

