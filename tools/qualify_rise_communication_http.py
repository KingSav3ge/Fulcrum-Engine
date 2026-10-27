"""Exercise ordinary Rise review, creation and speech against explicit App/Engine roots."""
import json
from pathlib import Path
import tempfile
import threading
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener
from server import make_server, Store

with tempfile.TemporaryDirectory(prefix='irgs-rise-ordinary-http-') as temporary:
    root = Path(temporary); store = Store(root/'saves')
    with patch('solo_provider.CapabilityBroker.dispatch', side_effect=AssertionError('provider called')), \
         patch('openai_proposals.OpenAIProposalTransport.__call__', side_effect=AssertionError('transport called')), \
         patch('http.server.BaseHTTPRequestHandler.log_message'):
        host = make_server(0, store.folder, reference_config=root/'no-personal-config.json',
                           reference_cache=root/'cache', solo_configuration=None)
        thread = threading.Thread(target=host.serve_forever, daemon=True); thread.start()
        opener = build_opener(ProxyHandler({})); base = 'http://127.0.0.1:' + str(host.server_port); token = None
        def http(path, body=None):
            request = Request(base+path, headers={'Content-Type': 'application/json',
                **({'X-IRGS-Token': token} if token else {})},
                data=None if body is None else json.dumps(body).encode())
            try:
                with opener.open(request, timeout=15) as reply: return reply.status, json.load(reply)
            except HTTPError as error: return error.code, json.load(error)
        try:
            status, session = http('/api/campaigns'); assert status == 200; token = session['token']
            selection = {'template_id': 'R00', 'founder_name': 'Synthetic Ari', 'household_name': 'Synthetic home',
                'settlement_name': 'Synthetic camp', 'region_name': 'Greywater Reach', 'date_label': 'Spring, Year 1',
                'company': 'solo', 'permission': 'seek', 'supplies': 'basic'}
            status, review = http('/api/rise/preview', {'choices': selection}); assert status == 200, review
            assert 'no response, consent or transfer is automatic' in review['neighbors']
            assert not list(store.folder.glob('*.json'))
            create = {'name': 'Synthetic Rise', 'choices': selection, 'review_digest': review['review_digest'],
                      'request_id': 'rise-ordinary-create'}
            status, created = http('/api/rise/create', create); assert status == 200, created
            key = created['id']; saved = store.path(key).read_bytes()
            status, replay = http('/api/rise/create', create)
            assert status == 200 and replay['id'] == key and store.path(key).read_bytes() == saved
            status, view = http('/api/playthrough/'+key); assert status == 200, view
            actor = view['actor_id']; control = view['communication_control']
            channel = next(c for c in control['channels'] if c['channel_id'] == 'commons-local')
            assert [p['actor_id'] for p in channel['participants']] == ['elin', 'oren']
            body = {'id': key, 'actor': actor, 'revision': view['revision'], 'view_token': control['view_token'],
                'request_id': 'rise-ordinary-speech', 'channel_id': 'commons-local', 'recipient': 'oren',
                'command': 'speak', 'details': {}, 'intention': 'I would like to ask about the clearing.'}
            status, packet = http('/api/communication/prepare', body); assert status == 200, packet
            accept = {'id': key, 'actor': actor, 'request_id': body['request_id'], 'explicitly_accepted': True}
            status, result = http('/api/communication/execute', accept); assert status == 200, result
            assert result['communication']['truth_status'] == 'testimony'
            saved = store.path(key).read_bytes(); assert http('/api/communication/execute', accept) == (200, result)
            assert store.path(key).read_bytes() == saved
            reloaded = Store(store.folder).read(key)['state']
            assert reloaded['communication_results'][body['request_id']]['status'] == 'testimony_received'
            assert reloaded['elapsed_time']['seconds'] == 0
            print(json.dumps({'status': 'PASS', 'review_create_speech_retry_reload': True, 'provider_calls': 0}))
        finally:
            host.shutdown(); host.server_close(); thread.join(timeout=5)
