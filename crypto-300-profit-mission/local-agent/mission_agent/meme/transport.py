"""Existing private repo/branches; immutable files before atomic current CAS pointer."""
from ..transport.github import GitHubTransport,RemoteError,Conflict,GitHubAPI
from ..hashing import canonical,seal,digest,verify
from .schema import validate_run

class MemeAPI(GitHubAPI):
    def request(self,method,endpoint,body=None):
        if method=='PUT':body={**body,'message':'Meme FM4 immutable GPT handoff'}
        return super().request(method,endpoint,body)

class MemeTransport(GitHubTransport):
    def __init__(self,namespace,*,test_id=None,api=None,live_validator=None):
        if namespace not in ('LIVE','TEST'):raise ValueError('NAMESPACE')
        super().__init__('mac',test_id or 'meme',api=api or MemeAPI())
        self.namespace='runtime-v2/meme' if namespace=='LIVE' else 'runtime-v2-test/meme/'+str(test_id or 'fm4')
        self.data_namespace=namespace;self.live_validator=live_validator
    def publish_run(self,run,sequence):
        validate_run(run,namespace=self.data_namespace)
        if type(sequence) is not int or sequence<1:raise ValueError('MANIFEST_SEQUENCE')
        if self.data_namespace=='LIVE':
            if self.live_validator is None:raise ValueError('REAL_FORWARD_VALIDATOR_REQUIRED')
            self.live_validator(run)
        base=self.namespace+'/runs/'+run['run_id']
        renderer=seal({'schema_version':2,'namespace':self.data_namespace,'run_id':run['run_id'],'candidate_bundle_sha256':run['payload_sha256'],'decisions_source':'gpt-data:'+self.namespace+'/decisions/'+run['run_id']+'.json','enrichment_source':'CURRENT_RUN_ONLY','previous_content_allowed':False})
        receipt=seal({'schema_version':2,'namespace':self.data_namespace,'run_id':run['run_id'],'candidate_bundle_sha256':run['payload_sha256'],'renderer_input_sha256':renderer['payload_sha256'],'verification_contract':'EXACT_CANONICAL_HASH_READBACK_BEFORE_MANIFEST'})
        values={'candidate-bundle.json':run,'renderer-input.json':renderer,'transport-receipt.json':receipt}
        for name,value in values.items():
            self.write(self.branch,base+'/'+name,value,immutable=True)
            if self.read(self.branch,base+'/'+name).data!=canonical(value):raise ValueError('EXACT_RUN_READBACK_FAILED')
        pointer=seal({'schema_version':2,'namespace':self.data_namespace,'run_id':run['run_id'],'sequence':sequence,'candidate_bundle_path':base+'/candidate-bundle.json','candidate_bundle_sha256':run['payload_sha256'],'expires_at':run['expires_at'],'status':'CURRENT_CANDIDATES' if run['candidates'] else 'NO_CURRENT_SIGNALS'})
        path=self.namespace+'/manifest/current.json';old=self._optional(self.branch,path)
        if old:
            verify(old.value)
            if old.value['sequence']>sequence:raise Conflict('MANIFEST_ROLLBACK_BLOCKED')
            if old.value['sequence']==sequence and old.data!=canonical(pointer):raise Conflict('SEQUENCE_IDENTITY_CONFLICT')
        self.write(self.branch,path,pointer,expected_sha=old.blob_sha if old else None)
        if self.read(self.branch,path).data!=canonical(pointer):raise ValueError('EXACT_MANIFEST_READBACK_FAILED')
        return {'run_id':run['run_id'],'sequence':sequence,'exact_readback':True,'namespace':self.namespace,'hash':run['payload_sha256']}
