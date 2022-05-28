import asyncio

class Events:

    def __init__(self, controller):
        self.controller = controller
        self.queue = asyncio.Queue()
        self.__listeners = {}
        self.__events = set()
        self.task = asyncio.create_task(self.__loop())

    async def __loop(self):
        ''' main event dispatch loop '''
        while True:
            event = await self.queue.get()
            await self.__dispatch(event)
            self.queue.task_done()

    async def __update_events(self):
        ''' send SETEVENTS command when set of event listeners changes '''
        events = set(self.__listeners.keys())
        if events != self.__events:
            self.__events = events
            eventstr = ' '.join(events)
            resp = await self.controller.io.cmd('SETEVENTS ' + eventstr)
            if resp['status'] != 250:
                raise Exception('unable to send SETEVENTS')

    async def add(self, event, listener):
        ''' add listener for event type '''
        if event not in self.__listeners:
            self.__listeners[event] = set()
        self.__listeners[event].add(listener)
        await self.__update_events()

    async def remove(self, event, listener):
        ''' remove listener for event type '''
        if event in self.__listeners:
            self.__listeners[event].discard(listener)
            if len(self.__listeners[event]) == 0:
                del self.__listeners[event]
        await self.__update_events()

    async def __dispatch(self, event):
        ''' dispatch event '''
        if event.type in self.__listeners:
            for listener in self.__listeners[event.type]:
                await listener(event)


class Event:
    pass


class BandwidthEvent(Event):

    type = 'BW'

    def __init__(self, read, written, **kwargs):
        self.read = read
        self.written = written
        self.kwargs = kwargs


class CircuitEvent(Event):

    type = 'CIRC'

    def __init__(self, id, status, path=None, **kwargs):
        self.id = id
        self.status = status
        self.path = path
        self.kwargs = kwargs


class StreamEvent(Event):

    type = 'STREAM'

    def __init__(self, id, status, circ_id, target, **kwargs):
        self.id = id
        self.status = status
        self.circ_id = circ_id
        self.target = target
        self.kwargs = kwargs


class AddrMapEvent(Event):

    type = 'ADDRMAP'

    def __init__(self, hostname, destination, expiry, **kwargs):
        self.hostname = hostname
        self.destination = destination
        self.expiry = expiry
        self.kwargs = kwargs


class HiddenServiceEvent(Event):

    type = 'HS_DESC'

    def __init__(self, *args, **kwargs):
        self.action = args[0]
        self.address = args[1]
        self.authentication = args[2]
        self.directory = args[3]
        if len(args) > 4:
            self.descriptor_id = args[4]
        else:
            self.descriptor_id = None
        self.kwargs = kwargs


class StreamBandwidthEvent(Event):

    type = 'STREAM_BW'

    def __init__(self, id, written, read, time, **kwargs):
        self.id = id
        self.written = written
        self.read = read
        self.time = time
        self.kwargs = kwargs


class NetworkLivenessEvent(Event):

    type = 'NETWORK_LIVENESS'

    def __init__(self, status, **kwargs):
        self.status = status
        self.kwargs = kwargs


class GuardEvent(Event):

    type = 'GUARD'

    def __init__(self, guard_type, endpoint, status, **kwargs):
        self.guard_type = guard_type
        self.endpoint = endpoint
        self.status = status
        self.kwargs = kwargs


class SignalEvent(Event):

    type = 'SIGNAL'

    def __init__(self, signal, **kwargs):
        self.signal = signal
        self.kwargs = kwargs


class OrConnEvent(Event):

    type = 'ORCONN'

    def __init__(self, endpoint, status, **kwargs):
        self.endpoint = endpoint
        self.status = status
        self.kwargs = kwargs


class CircMinorEvent(Event):

    type = 'CIRC_MINOR'

    def __init__(self, id, event, path=None, **kwargs):
        self.id = id
        self.event = event
        self.path = path
        self.kwargs = kwargs


class StatusGeneralEvent(Event):

    type = 'STATUS_GENERAL'

    def __init__(self, runlevel, action, **kwargs):
        self.runlevel = runlevel
        self.action = action
        self.kwargs = kwargs


class StatusClientEvent(Event):

    type = 'STATUS_CLIENT'

    def __init__(self, runlevel, action, **kwargs):
        self.runlevel = runlevel
        self.action = action
        self.kwargs = kwargs


class StatusServerEvent(Event):

    type = 'STATUS_SERVER'

    def __init__(self, runlevel, action, **kwargs):
        self.runlevel = runlevel
        self.action = action
        self.kwargs = kwargs


class HSDescContentEvent(Event):

    type = 'HS_DESC_CONTENT'

    def __init__(self, address, descriptor_id, directory, **kwargs):
        self.address = address
        self.descriptor_id = descriptor_id
        self.directory = directory
        self.kwargs = kwargs


class TransportLaunchedEvent(Event):

    type = 'TRANSPORT_LAUNCHED'

    def __init__(self, transport_type, name, address, port, **kwargs):
        self.transport_type = transport_type
        self.name = name
        self.address = address
        self.port = port
        self.kwargs = kwargs


# registered event types
EVENT_TYPES = {
    'BW': BandwidthEvent,
    'CIRC': CircuitEvent,
    'STREAM': StreamEvent,
    'ADDRMAP': AddrMapEvent,
    'HS_DESC': HiddenServiceEvent,
    'STREAM_BW': StreamBandwidthEvent,
    'NETWORK_LIVENESS': NetworkLivenessEvent,
    'GUARD': GuardEvent,
    'SIGNAL': SignalEvent,
    'ORCONN': OrConnEvent,
    'CIRC_MINOR': CircMinorEvent,
    'STATUS_GENERAL': StatusGeneralEvent,
    'STATUS_CLIENT': StatusClientEvent,
    'STATUS_SERVER': StatusServerEvent,
    'HS_DESC_CONTENT': HSDescContentEvent,
    'TRANSPORT_LAUNCHED': TransportLaunchedEvent,
}
