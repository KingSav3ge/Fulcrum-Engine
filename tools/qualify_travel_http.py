"""Ordinary Rise host travel using explicit Engine and App source roots."""
import json
from pathlib import Path
import tempfile
import threading
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener
from server import make_server, Store

with tempfile.TemporaryDirectory(prefix='irgs-travel-http-') as directory:
    root=Path(directory); store=Store(root/'saves')
    with patch('solo_provider.CapabilityBroker.dispatch',side_effect=AssertionError('provider called')), \
         patch('openai_proposals.OpenAIProposalTransport.__call__',side_effect=AssertionError('transport called')), \
         patch('http.server.BaseHTTPRequestHandler.log_message'):
        host=make_server(0,store.folder,reference_config=root/'no-personal-config.json',reference_cache=root/'cache',solo_configuration=None)
        thread=threading.Thread(target=host.serve_forever,daemon=True);thread.start()
        opener=build_opener(ProxyHandler({}));base='http://127.0.0.1:'+str(host.server_port);token=None
        def http(path,body=None):
            request=Request(base+path,headers={'Content-Type':'application/json',**({'X-IRGS-Token':token} if token else {})},data=None if body is None else json.dumps(body).encode())
            try:
                with opener.open(request,timeout=15) as reply:return reply.status,json.load(reply)
            except HTTPError as error:return error.code,json.load(error)
        try:
            code,session=http('/api/campaigns');assert code==200;token=session['token']
            choices={'template_id':'R00','founder_name':'Synthetic founder','household_name':'Synthetic home',
                'settlement_name':'Synthetic camp','region_name':'Greywater Reach','date_label':'Spring, Year 1',
                'company':'sibling','permission':'seek','supplies':'basic'}
            code,review=http('/api/rise/preview',{'choices':choices});assert code==200,review
            code,created=http('/api/rise/create',{'name':'Synthetic travel','choices':choices,
                'review_digest':review['review_digest'],'request_id':'travel-create'});assert code==200,created
            key=created['id']; parent=None
            def view():
                code,result=http('/api/playthrough/'+key);assert code==200,result;return result
            def phase(command,identity,details=None):
                current=view(); control=current['process_control']
                body={'id':key,'actor':'founder','revision':current['revision'],'view_token':control['view_token'],
                    'request_id':identity,'command':command,'intention':'I explicitly request '+command+'.'}
                if command=='start':
                    option=next(o for o in control['start_options'] if o['kind']=='travel' and o['action_id']=='walk_clearing')
                    body['capability_id']=option['capability_id']
                else:
                    body.update(process_id=parent,details=details or {})
                code,prepared=http('/api/process/prepare',body);assert code==200,(code,prepared)
                accepted={'id':key,'actor':'founder','request_id':identity,'explicitly_accepted':True}
                code,result=http('/api/process/execute',accepted);assert code==200,(code,result)
                return result,accepted
            start,_=phase('start','travel-start');parent=start['process']['process_id']
            assert start['process']['kind']=='travel'
            assert store.read(key)['state']['stock_accounts']['founder-home']['site']=='route:commons-clearing'
            partial,_=phase('advance','travel-partial',{'seconds':100});assert partial['process']['worked_seconds']==100
            paused,_=phase('pause','travel-pause');assert paused['process']['status']=='paused'
            assert 'cancel' not in view()['process_control']['processes'][0]['commands']
            phase('resume','travel-resume')
            final,accepted=phase('advance','travel-arrive',{'seconds':1000})
            assert final['process']['status']=='completed' and final['process']['elapsed_total']==300
            saved=store.path(key).read_bytes();assert http('/api/process/execute',accepted)==(200,final)
            assert store.path(key).read_bytes()==saved
            state=Store(store.folder).read(key)['state']
            assert state['actors']['founder']['current']['location']=='clearing'
            assert state['actors']['rowan']['current']['location']=='clearing'
            assert state['stock_accounts']['founder-home']['site']=='clearing'
            assert 'process-arrival:'+parent in state['settlement_receipts']['founder']
            print(json.dumps({'status':'PASS','ordinary_create':True,'partial_pause_resume_arrival':True,'retry_reload':True,'provider_calls':0}))
        finally:
            host.shutdown();host.server_close();thread.join(timeout=5)
