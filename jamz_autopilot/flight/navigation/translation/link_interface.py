from abc import ABC, abstractmethod


class LinkInterface (ABC):

    # abstract method goto directs drone go to a given location
    def goto(self, command):
        return

    # abstract method ascend directs drone to ascend to a level
    def ascend(self, command):
        return

    # abstract method ascend directs drone to descend to a level
    def descend(self, command):
        return