import asyncio
from .events import EVENT_TYPES

class Parser:

    def __init__(self):
        self.index = 0
        self.text = ''
        self.key = ''
        self.value = ''
        self.args = []
        self.kwargs = {}

    def parse(self, text):
        ''' Parse text for args and kwargs '''
        self.index = 0
        self.text = text
        while self.index < len(self.text):
            c = self.pop()
            if c == ' ':
                self._flush()
                continue
            elif c == '"':
                if not self.value:
                    self._parse_quoted()
                    self._flush()
                    continue
            elif c == '=':
                if not self.key:
                    self.key = self.value
                    self.value = ''
                    continue
            elif c == '+':
                if not self.value:
                    a = self.text.index('=\r\n', self.index)
                    key = self.text[self.index:a]
                    a += 3
                    b = self.text.index('.\r\n', a)
                    value = self.text[a:b]
                    b += 3
                    self.index = b
                    self.kwargs[key] = value
                    continue
            self.value += c
        self._flush()

    def parse_keywords(self, text):
        ''' Parse only keyword response text (used in getinfo responses) '''
        self.index = 0
        self.text = text
        while self.index < len(self.text):
            c = self.pop()
            if c == '"':
                if not self.value:
                    self._parse_quoted()
                    self._flush()
                    continue
            elif c == '=':
                if not self.key:
                    self.key = self.value
                    try:
                        a = self.text.index('\r\n', self.index)
                    except ValueError:
                        a = -1
                    if a > -1:
                        self.value = self.text[self.index:a]
                        self._flush()
                        self.index = a + 3
                        continue
                    else:
                        self.value = self.text[self.index:]
                        self._flush()
                        break
            elif c == '+':
                if not self.value:
                    a = self.text.index('=\r\n', self.index)
                    key = self.text[self.index:a]
                    a += 3
                    b = self.text.index('.\r\n', a)
                    value = self.text[a:b]
                    b += 3
                    self.index = b
                    self.kwargs[key] = value
                    continue
            self.value += c
        self._flush()
        if self.key:
            self.kwargs[self.key] = ''

    def _flush(self):
        if self.value:
            if self.key:
                self.kwargs[self.key] = self.value
                self.key = ''
            else:
                self.args.append(self.value)
            self.value = ''

    def _parse_quoted(self):
        while True:
            c = self.pop()
            if c == '\\':
                self.value += self.pop()
            elif c == '"':
                return
            else:
                self.value += c

    def pop(self):
        c = self.text[self.index]
        self.index += 1
        return c


def parse(text):
    ''' parse text and return args, kwargs '''
    p = Parser()
    p.parse(text)
    return p.args, p.kwargs

def parse_keywords(text):
    ''' parse text and return only kwargs '''
    p = Parser()
    p.parse_keywords(text)
    return p.kwargs


class TextProtocol:

    def __init__(self, r, w, event_queue=None):
        self.r = r
        self.w = w
        self.response_queue = asyncio.Queue()
        self.event_queue = event_queue
        self.lock = asyncio.Lock()
        self.task = asyncio.create_task(self.__loop())

    async def __loop(self):
        ''' main reader loop '''
        while True:
            resp = await self.__read()
            if resp['status'] == 650:
                await self.__put_event(resp)
            else:
                await self.response_queue.put(resp)

    async def __put_event(self, resp):
        ''' parse and queue an event from a resp object '''
        if self.event_queue is None:
            return
        args, kwargs = parse(' '.join(resp['lines']))
        type, args = args[0], args[1:]
        if type in EVENT_TYPES:
            event = EVENT_TYPES[type](*args, **kwargs)
            await self.event_queue.put(event)

    async def __write(self, cmd):
        ''' writes a command '''
        self.w.write(cmd.encode('utf8') + b'\r\n')
        await self.w.drain()

    async def __read(self):
        ''' reads a response '''
        lines = []
        status = -1
        while True:
            line = await self.r.readline()
            # make sure line starts with valid status code
            try:
                status = int(line[:3])
            except ValueError:
                status = -1
                break
            # don't append trailing OK line
            if line[3:4] == b' ' and line[4:] == b'OK\r\n':
                break
            # + multiline response
            if line[3:4] == b'+':
                data = line[3:]
                while True:
                    line = await self.r.readline()
                    data += line
                    if line == b'.\r\n':
                        break
                lines.append(data.decode('utf8'))
                continue
            lines.append(line[4:].decode('utf8').strip())
            # if not multiline response, exit
            if line[3:4] != b'-':
                break
        return {'status': status, 'lines': lines}

    async def cmd(self, cmd):
        ''' send a command and return response object '''
        async with self.lock:
            await self.__write(cmd)
            resp = await self.response_queue.get()
            self.response_queue.task_done()
            return resp
