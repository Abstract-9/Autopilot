

from abc import ABC, abstractmethod
from jamz_autopilot.flight.navigation.Controller import Controller

class LinkInterface (ABC) :

    #Controller class variable
    controller = Controller.initialize()

    #absract method goTo directs drone go to a given location
    def goTo(self):
        return

    #absract method ascend directs drone to ascend to a level
    def ascend(self):
        return

    # absract method ascend directs drone to descend to a level
    def descend(self):
        return