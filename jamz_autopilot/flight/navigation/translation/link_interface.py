from abc import ABC, abstractmethod


class LinkInterface (ABC):

    #absract method goTo directs drone go to a given location
    def goto(self, command):
        return

    #absract method ascend directs drone to ascend to a level
    def ascend(self, command):
        return

    # absract method ascend directs drone to descend to a level
    def descend(self, command):
        return