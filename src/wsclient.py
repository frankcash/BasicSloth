import base64
import binascii
import datetime
import email.utils
import hashlib
import hmac
import json
import os
import pprint
import struct
import sys
import urllib.parse
import uuid

import asyncio

import aiohttp
from aiohttp import websocket

try:
    import speex
except:
    speex = None


WS_KEY = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

class WebsocketConnection:
    MSG_JSON = 1
    MSG_AUDIO = 2

    @asyncio.coroutine
    def connect(self, url, app_id, app_key, use_plaintext=True):
        date = datetime.datetime.utcnow()
        sec_key = base64.b64encode(os.urandom(16))

        if use_plaintext:
            params = {'app_id': app_id, 'algorithm': 'key', 'app_key': binascii.hexlify(app_key)}
        else:
            datestr = date.replace(microsecond=0).isoformat()
            params = {
                'date': datestr,
                'app_id': app_id,
                'algorithm': 'HMAC-SHA-256',
                'signature': hmac.new(app_key,datestr.encode('ascii')+b' '+app_id.encode('utf-8'),hashlib.sha256).hexdigest()
            }

        response = yield from aiohttp.request(
            'get', url + '?' + urllib.parse.urlencode(params),
            headers={
                'UPGRADE': 'WebSocket',
                'CONNECTION': 'Upgrade',
                'SEC-WEBSOCKET-VERSION': '13',
                'SEC-WEBSOCKET-KEY': sec_key.decode(),
            })

        if response.status == 401 and not use_plaintext:
            if 'Date' in response.headers:
                server_date = email.utils.parsedate_to_datetime(response.headers['Date'])
                if server_date.tzinfo is not None:
                    server_date = (server_date - server_date.utcoffset()).replace(tzinfo=None)
            else:
                server_date = yield from response.read()
                server_date = datetime.datetime.strptime(server_date[:19].decode('ascii'), "%Y-%m-%dT%H:%M:%S")

            # Use delta on future requests
            date_delta = server_date - date

            print("Retrying authorization (delta=%s)" % date_delta)

            datestr = (date+date_delta).replace(microsecond=0).isoformat()
            params = {
                'date': datestr,
                'algorithm': 'HMAC-SHA-256',
                'app_id': app_id,
                'signature': hmac.new(app_key,datestr.encode('ascii')+b' '+app_id.encode('utf-8'),hashlib.sha256).hexdigest()
            }

            response = yield from aiohttp.request(
                'get', url + '?' + urllib.parse.urlencode(params),
                headers={
                    'UPGRADE': 'WebSocket',
                    'CONNECTION': 'Upgrade',
                    'SEC-WEBSOCKET-VERSION': '13',
                    'SEC-WEBSOCKET-KEY': sec_key.decode(),
                })


        if response.status != 101:
            info = "%s %s\n" % (response.status, response.reason)
            for (k,v) in response.headers.items():
                info += '%s: %s\n' % (k,v)
            info += '\n%s' % (yield from response.read()).decode('utf-8')

            if response.status == 401:
                raise RuntimeError("Authorization failure:\n%s" % info)
            elif response.status >= 500 and response.status < 600:
                raise RuntimeError("Server error:\n%s" %  info)
            elif response.headers.get('upgrade', '').lower() != 'websocket':
                raise ValueError("Handshake error - Invalid upgrade header")
            elif response.headers.get('connection', '').lower() != 'upgrade':
                raise ValueError("Handshake error - Invalid connection header")
            else:
                raise ValueError("Handshake error: Invalid response status:\n%s" % info)


        key = response.headers.get('sec-websocket-accept', '').encode()
        match = base64.b64encode(hashlib.sha1(sec_key + WS_KEY).digest())
        if key != match:
            raise ValueError("Handshake error - Invalid challenge response")

        # switch to websocket protocol
        self.connection = response.connection
        self.stream = self.connection.reader.set_parser(websocket.WebSocketParser)
        self.writer = websocket.WebSocketWriter(self.connection.writer)
        self.response = response

    @asyncio.coroutine
    def receive(self):
        wsmsg = yield from self.stream.read()
        if wsmsg.tp == 1:
            return (self.MSG_JSON, json.loads(wsmsg.data))
        else:
            return (self.MSG_AUDIO, wsmsg.data)

    def send_message(self, msg):
        log(msg,sending=True)
        self.writer.send(json.dumps(msg))

    def send_audio(self, audio):
        self.writer.send(audio, binary=True)

    def close(self):
        self.writer.close()
        self.response.close()
        self.connection.close()

def log(obj,sending=False):
    print('>>>>' if sending else '<<<<')
    print('%s' % datetime.datetime.now())
    pprint.pprint(obj)
    print()


@asyncio.coroutine
def do_understand_text(loop, url, app_id, app_key, context_tag, text_to_understand, use_speex=None):

    if use_speex is True and speex is None:
        print('ERROR: Speex encoding specified but python-speex module unavailable')
        return

    if use_speex is not False and speex is not None:
        audio_type = 'audio/x-speex;mode=wb'
    else:
        audio_type = 'audio/L16;rate=16000'

    client = WebsocketConnection()
    yield from client.connect(url, app_id, app_key)

    client.send_message({
        'message': 'connect',
        'device_id': '55555500000000000000000000000000',
        'codec': audio_type
    })

    tp, msg = yield from client.receive()
    log(msg) # Should be a connected message

    client.send_message({
        'message': 'query_begin',
        'transaction_id': 123,

        'command': 'NDSP_APP_CMD',
        'language': 'eng-USA',
        'context_tag': context_tag,
    })

    client.send_message({
        'message': 'query_parameter',
        'transaction_id': 123,

        'parameter_name': 'REQUEST_INFO',
        'parameter_type': 'dictionary',

        'dictionary': {
            'application_data': {
                'text_input': text_to_understand,
            }
        }
    })

    client.send_message({
        'message': 'query_end',
        'transaction_id': 123,
    })

    while True:
        tp,msg = yield from client.receive()
        log(msg)

        if msg['message'] == 'query_end':
            break

    client.close()

@asyncio.coroutine
def do_understand(loop, url, app_id, app_key, context_tag, input_file, use_speex=None):

    if use_speex is True and speex is None:
        print('ERROR: Speex encoding specified but python-speex module unavailable')
        return

    if use_speex is not False and speex is not None:
        audio_type = 'audio/x-speex;mode=wb'
    else:
        audio_type = 'audio/L16;rate=16000'

    client = WebsocketConnection()
    yield from client.connect(url, app_id, app_key)

    client.send_message({
        'message': 'connect',
        'device_id': '55555500000000000000000000000000',
        'codec': audio_type
    })

    tp, msg = yield from client.receive()
    log(msg) # Should be a connected message

    client.send_message({
        'message': 'query_begin',
        'transaction_id': 123,

        'command': 'NDSP_ASR_APP_CMD',
        'language': 'eng-USA',
        'context_tag': context_tag,
    })

    client.send_message({
        'message': 'query_parameter',
        'transaction_id': 123,

        'parameter_name': 'AUDIO_INFO',
        'parameter_type': 'audio',

        'audio_id': 456
    })

    client.send_message({
        'message': 'query_end',
        'transaction_id': 123,
    })

    client.send_message({
        'message': 'audio',
        'audio_id': 456,
    })

    if audio_type == 'audio/x-speex;mode=wb':
        # wide-band speex
        encoder = speex.WBEncoder()
        frame_size = encoder.frame_size * 2 # two bytes per sample
        with open(input_file, 'rb') as f:
            while f.readable():
                data = f.read(frame_size)
                if  len(data) < frame_size:
                    break
                coded = encoder.encode(data)
                client.send_audio(coded)

    elif audio_type.split(';')[0] == 'audio/L16':
        # raw PCM
        with open(input_file, 'rb') as f:
            while f.readable():
                data = f.read(2000)
                if len(data) == 0:
                    break
                client.send_audio(data)

    else:
        print('ERROR: Need to implement encoding for %s!' % audio_type)
        return

    client.send_message({
        'message': 'audio_end',
        'audio_id': 456,
    })

    while True:
        tp,msg = yield from client.receive()
        log(msg)

        if msg['message'] == 'query_end':
            break

    client.close()

@asyncio.coroutine
def do_recognize(loop, url, app_id, app_key, reco_model, input_file, use_speex=None):

    if use_speex is True and speex is None:
        print('ERROR: Speex encoding specified but python-speex module unavailable')
        return

    if use_speex is not False and speex is not None:
        audio_type = 'audio/x-speex;mode=wb'
    else:
        audio_type = 'audio/L16;rate=16000'

    client = WebsocketConnection()
    yield from client.connect(url, app_id, app_key)

    client.send_message({
        'message': 'connect',
        'device_id': '55555500000000000000000000000000',
        'codec': audio_type,
    })

    tp, msg = yield from client.receive()
    log(msg) # Should be a connected message

    client.send_message({
        'message': 'query_begin',
        'transaction_id': 123,

        'command': 'NVC_ASR_CMD', #'NDSP_ASR_APP_CMD',
        'language': 'eng-USA',
        'recognition_type': reco_model,
    })

    client.send_message({
        'message': 'query_parameter',
        'transaction_id': 123,

        'parameter_name': 'AUDIO_INFO',
        'parameter_type': 'audio',

        'audio_id': 456
    })

    client.send_message({
        'message': 'query_end',
        'transaction_id': 123,
    })

    client.send_message({
        'message': 'audio',
        'audio_id': 456,
    })

    if audio_type == 'audio/x-speex;mode=wb':
        # wide-band speex
        encoder = speex.WBEncoder()
        frame_size = encoder.frame_size * 2 # two bytes per sample
        with open(input_file, 'rb') as f:
            while f.readable():
                data = f.read(frame_size)
                if  len(data) < frame_size:
                    break
                coded = encoder.encode(data)
                client.send_audio(coded)

    elif audio_type.split(';')[0] == 'audio/L16':
        # raw PCM
        with open(input_file, 'rb') as f:
            while f.readable():
                data = f.read(2000)
                if len(data) == 0:
                    break
                client.send_audio(data)

    else:
        print('ERROR: Need to implement encoding for %s!' % audio_type)
        return

    client.send_message({
        'message': 'audio_end',
        'audio_id': 456,
    })

    while True:
        tp,msg = yield from client.receive()
        log(msg)

        if msg['message'] == 'query_end':
            break

    client.close()


def do_synthesis(loop, url, app_id, app_key, input_text, output_file, use_speex=None):

    if use_speex is True and speex is None:
        print('ERROR: Speex encoding specified but python-speex module unavailable')
        return

    if use_speex is not False and speex is not None:
        audio_type = 'audio/x-speex;mode=wb'
    else:
        audio_type = 'audio/L16;rate=16000'

    client = WebsocketConnection()
    yield from client.connect(url, app_id, app_key)

    client.send_message({
        'message': 'connect',
        'device_id': '55555500000000000000000000000000',
        'codec': audio_type,
    })

    tp, msg = yield from client.receive()
    log(msg) # Should be a connected message

    # synthesize
    client.send_message({
        'message': 'query_begin',
        'transaction_id': 123,

        'command': 'NMDP_TTS_CMD',
        'language': 'eng-USA',
        #'tts_voice': 'ava',
    })

    client.send_message({
        'message': 'query_parameter',
        'transaction_id': 123,

        'parameter_name': 'TEXT_TO_READ',
        'parameter_type': 'dictionary',
        'dictionary': {
            'audio_id': 789,
            'tts_input': input_text,
            'tts_type': 'text'
        }
    })

    client.send_message({
        'message': 'query_end',
        'transaction_id': 123,
    })

    with open(output_file, 'wb') as f:
        if audio_type.split(';')[0] == 'audio/L16':
            decoder = None
        elif audio_type == 'audio/x-speex;mode=wb':
            decoder = speex.WBDecoder()
        else:
            print('ERROR: Need to implement decoding of %s!' % audio_type)

        while True:
            tp,msg = yield from client.receive()

            if tp == client.MSG_JSON:
                log(msg)
                if msg['message'] == 'query_end':
                    break
            else:
                log('Got %d bytes of audio' % len(msg))
                if decoder is not None:
                    pcm = decoder.decode(msg)
                    f.write(pcm)
                else:
                    f.write(msg)

    f.close()
    client.close()

def main():
    url = 'https://httpapi.labs.nuance.com/v1'

    f = open(sys.argv[1],'r')
    credentials = json.load(f)
    f.close()

    loop = asyncio.get_event_loop()

    if sys.argv[2] == 'understand':
        loop.run_until_complete(do_understand(
            loop, url,
            credentials['app_id'],
            binascii.unhexlify(credentials['app_key']),
            context_tag=sys.argv[3],
            input_file=sys.argv[4]))

    elif sys.argv[2] == 'understand_text':
        loop.run_until_complete(do_understand_text(
            loop, url,
            credentials['app_id'],
            binascii.unhexlify(credentials['app_key']),
            context_tag=sys.argv[3],
            text_to_understand=sys.argv[4]))

    elif sys.argv[2] == 'recognize':
        loop.run_until_complete(do_recognize(
            loop, url,
            credentials['app_id'],
            binascii.unhexlify(credentials['app_key']),
            reco_model=sys.argv[3],
            input_file=sys.argv[4]))

    elif sys.argv[2] == 'synthesize':
        loop.run_until_complete(do_synthesis(
            loop, url,
            credentials['app_id'],
            binascii.unhexlify(credentials['app_key']),
            input_text=sys.argv[3],
            output_file=sys.argv[4]))

    else:
        return


if __name__ == '__main__':
    main()
