import asyncio

class Core:

    flightEvent = asyncio.Event
    commsEvent = asyncio.Event

    def initializeFlight():
        #return Autopilot object
        return 0


    def initializeComms():
        #return Comms object
        return 0

    
    def onFlightEvent():
        #return none
        return 0

    def onCommsEvent():
        #return none
        return 0


def main():
    print("Hello World!")

if __name__ == "__main__":
    main()