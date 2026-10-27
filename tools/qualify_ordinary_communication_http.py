"""Exercise reviewed ordinary App creation and speech against explicit source roots.

Run with IRGS_ENGINE_ROOT, IRGS_CATALOG_ROOT and App/runtime PYTHONPATH set.
The host uses a temporary store, explicit temporary reference paths and no provider.
"""
import json,tempfile,threading
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,build_opener,ProxyHandler
from urllib.error import HTTPError
from unittest.mock import patch
from server import make_server,Store
from historical_campaigns import historical_entry

tmp=tempfile.TemporaryDirectory(prefix='alpha-ordinary-http-'); root=Path(tmp.name)
store=Store(root/'saves')
with patch('solo_provider.CapabilityBroker.dispatch',side_effect=AssertionError('unexpected provider')), patch('openai_proposals.OpenAIProposalTransport.__call__',side_effect=AssertionError('unexpected transport')), patch('http.server.BaseHTTPRequestHandler.log_message'):
    host=make_server(0,store.folder,reference_config=root/'no-config.json',reference_cache=root/'cache',solo_configuration=None)
    thread=threading.Thread(target=host.serve_forever,daemon=True);thread.start();opener=build_opener(ProxyHandler({}));base='http://127.0.0.1:'+str(host.server_port);token=None
    def http(path,body=None):
        req=Request(base+path,headers={'Content-Type':'application/json',**({'X-IRGS-Token':token} if token else {})},data=None if body is None else json.dumps(body).encode())
        try:
            with opener.open(req,timeout=15) as r:return r.status,json.load(r)
        except HTTPError as e:return e.code,json.load(e)
    try:
        status,session=http('/api/campaigns');assert status==200;token=session['token']
        select={'profile_id':'military','scenario_id':'hundred-years-war','entry_id':'hyw-1415','snapshot_sha256':historical_entry('hyw-1415')['snapshot_sha256']}
        status,options=http('/api/starting-options?'+urlencode(select));assert status==200
        opening=next(x for x in options['playable_openings'] if x['id']=='quay-contact-v1');assert opening['fictional']
        fields={**select,'selection_digest':options['selection_digest'],'starting_scenario_id':'individual','character_kind':'new','species':'human','opening_id':'quay-contact-v1'}
        status,review=http('/api/starting-preview?'+urlencode(fields));assert status==200,(status,review)
        assert not list(store.folder.glob('*.json'))
        body={**select,'name':'Synthetic ordinary HTTP','request_id':'alpha-create','character':{'kind':'new','name':'Synthetic courier','species':'human','opening_id':'quay-contact-v1'},'selection_digest':options['selection_digest'],'mode':'player'}
        status,created=http('/api/create',body);assert status==200,(status,created)
        initial=store.path(created['id']).read_bytes()
        repeated_status,repeated=http('/api/create',body)
        assert repeated_status==200 and repeated.get('id')==created['id'], (repeated_status,repeated)
        assert store.path(created['id']).read_bytes()==initial
        campaign=created['id'];status,view=http('/api/playthrough/'+campaign);assert status==200,(status,view)
        actor=view['actor_id'];control=view['communication_control'];participants=control['channels'][0]['participants'];assert [p['actor_id'] for p in participants]==['FICTIONAL-QUAY-CONTACT']
        speech={'id':campaign,'actor':actor,'revision':view['revision'],'view_token':control['view_token'],'request_id':'alpha-speak','channel_id':'quay-local','recipient':'FICTIONAL-QUAY-CONTACT','command':'speak','details':{},'intention':'Please show me where the desk is.'}
        status,prepared=http('/api/communication/prepare',speech);assert status==200,(status,prepared)
        accept={'id':campaign,'actor':actor,'request_id':'alpha-speak','explicitly_accepted':True}
        status,result=http('/api/communication/execute',accept);assert status==200,(status,result)
        assert result['communication']['truth_status']=='testimony'
        saved=store.path(campaign).read_bytes();assert http('/api/communication/execute',accept)==(200,result);assert store.path(campaign).read_bytes()==saved
        assert Store(store.folder).read(campaign)['state']['communication_results']['alpha-speak']['status']=='testimony_received'
        print(json.dumps({'status':'PASS','preview':200,'create':200,'speech':'testimony_received','exact_retry':True,'store_reload':True,'provider_calls':0}))
    finally:
        host.shutdown();host.server_close();thread.join();tmp.cleanup()
