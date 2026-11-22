"""Public linked-source claims, post relationships and exact-CA recognition."""
import base64
from collections import deque
from datetime import datetime,timezone
import hashlib
import json
from html.parser import HTMLParser
import re
import time
from urllib.parse import urlsplit
from .cluster import RPCJobBudgetExceeded
from .holder_ranks import valid_pubkey
from .public_html import canonical_url,read_public_html,read_public_json,MAX_HTML_BYTES


def clip(value,words,chars):return ' '.join(str(value or '').split()[:words])[:chars]


THEMES = (
    ('AI／模型训练', r'\b(?:ai|llms?|pretraining|machine learning|neural|artificial intelligence)\b'),
    ('爬虫／智能体', r'\b(?:crawlers?|agents?|autonomous bots?)\b'),
    ('动物／社区模因', r'\b(?:cats?|dogs?|frogs?|memes?|community)\b'),
    ('游戏／虚拟世界', r'\b(?:games?|gaming|metaverse|virtual world)\b'),
    ('文化／艺术', r'\b(?:artists?|artwork|art|culture)\b'),
)
ACTORS = (('ELON_MUSK', r'\belon\s+musk\b|(?<!\w)@elonmusk\b'),
          ('DONALD_TRUMP', r'\bdonald\s+trump\b|(?<!\w)@realdonaldtrump\b'),
          ('VITALIK_BUTERIN', r'\bvitalik\s+buterin\b|(?<!\w)@vitalikbuterin\b'))


def story_fields(text, links):
    """Describe source content; a name or post link never verifies interaction."""
    themes=[label for label,pattern in THEMES if re.search(pattern,text,re.I)]
    actors=[label for label,pattern in ACTORS if re.search(pattern,text,re.I)]
    if actors:themes.append('人物／事件关联说法')
    posts=[]
    for value in links:
        try:url=canonical_url(value)
        except ValueError:continue
        parsed=urlsplit(url)
        if parsed.hostname not in {'x.com','www.x.com','twitter.com','www.twitter.com'}:continue
        if re.fullmatch(r'/[A-Za-z0-9_]{1,30}/status/[0-9]+/?',parsed.path) is None:continue
        if url not in posts:posts.append(url)
    return {'version':1,'themes':themes,'actors_mentioned':actors,
            'interaction_status':'UNVERIFIED','post_links':posts,
            'post_links_scope':'PRESENT_IN_READ_PAGE; NOT_FOLLOWED_OR_AUTHOR_VERIFIED'}


def story_summary(evidence):
    themes=[]
    for row in evidence:
        for theme in row['story']['themes']:
            if theme not in themes:themes.append(theme)
    return {'version':1,'status':'SOURCE_CLAIMS' if evidence else 'UNAVAILABLE',
            'themes':themes,'sources_read':len(evidence),
            'interaction_status':'UNVERIFIED','official_recognition':'UNVERIFIED',
            'evidence_scope':'READ_SOURCE_CONTENT; NO_INDEPENDENT_EVENT_OR_AUTHOR_VERIFICATION'}


def story_excerpt(description,text):
    """Prefer a concrete source sentence over generic metadata, within 16 words."""
    candidates=[]
    for origin,value in enumerate((description,text)):
        for sentence in re.split(r'(?<=[.!?])\s+|[\r\n]+',value):
            sentence=' '.join(sentence.split())
            if len(sentence)<20:continue
            actor=any(re.search(pattern,sentence,re.I) for _,pattern in ACTORS)
            event=bool(re.search(r'\b(?:repl(?:y|ied)|interact\w*|liked?|repost\w*|retweet\w*|endors\w*|launch\w*)\b',sentence,re.I))
            complete=sentence[-1:] in '.!?' and len(sentence.split())<=16 and len(sentence)<=200
            candidates.append(((int(actor and event),int(complete),-origin),sentence))
    selected=max(candidates,key=lambda row:row[0])[1] if candidates else description or text
    excerpt=clip(selected,16,200)
    return excerpt[:199]+'…' if excerpt!=' '.join(selected.split()) else excerpt


class ClaimHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden=[];self.title=False;self.title_parts=[];self.text=[];self.meta={};self.language=None;self.links=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        void=tag in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
        if self.hidden:
            if not void:self.hidden.append(tag)
            return
        if tag in {'script','style','template','noscript'} or 'hidden' in attrs or str(attrs.get('aria-hidden') or '').lower()=='true':
            if not void:self.hidden.append(tag)
            return
        if tag in {'p','div','article','section','li','h1','h2','h3','br'}:self.text.append('\n')
        if tag=='a' and isinstance(attrs.get('href'),str):self.links.append(attrs['href'])
        if tag=='html':self.language=attrs.get('lang')
        if tag=='title':self.title=True
        if tag=='meta':
            key=(attrs.get('name') or attrs.get('property') or '').lower()
            if key and isinstance(attrs.get('content'),str) and key not in self.meta:self.meta[key]=attrs['content']
    def handle_endtag(self,tag):
        if self.hidden:
            if tag in self.hidden:
                index=len(self.hidden)-1-self.hidden[::-1].index(tag)
                del self.hidden[index:]
            return
        if tag=='title':self.title=False
        if tag in {'p','div','article','section','li','h1','h2','h3'}:self.text.append('\n')
    def handle_data(self,data):
        if self.hidden:return
        if self.title:self.title_parts.append(data)
        else:self.text.append(data)


def extract_page_claim(raw,url,mint,observed_at):
    if not isinstance(raw,bytes) or len(raw)>MAX_HTML_BYTES:raise ValueError('RESPONSE_LIMIT')
    try:document=raw.decode('utf-8')
    except UnicodeDecodeError:raise ValueError('RESPONSE_TEXT_INVALID') from None
    parser=ClaimHTML();parser.feed(document);parser.close()
    title=' '.join(parser.title_parts) or parser.meta.get('og:title') or parser.meta.get('twitter:title') or '';text=' '.join(parser.text)
    description=parser.meta.get('description') or parser.meta.get('og:description') or parser.meta.get('twitter:description') or ''
    combined=' '.join((title,text,description))
    if any(marker in combined.lower() for marker in ('just a moment','verify you are human','access denied','log in to x','enable javascript')):raise ValueError('ACCESS_WALL_OR_SCRIPT_ONLY')
    if str(parser.language or '').lower().startswith('zh'):raise ValueError('SOURCE_LANGUAGE_NOT_SELECTED')
    host=urlsplit(url).hostname or ''
    boilerplate=description.lower().strip()
    if (host in {'pump.fun','www.pump.fun'} and boilerplate.startswith(('launch and trade','create and trade'))) or (host in {'x.com','twitter.com','www.x.com','www.twitter.com'} and boilerplate.startswith(('from breaking news','happening now'))):raise ValueError('NO_EXTRACTABLE_CLAIM')
    claim=description.strip() or text.strip()
    if len(claim)<20:raise ValueError('NO_EXTRACTABLE_CLAIM')
    chinese=sum('\u4e00'<=c<='\u9fff' for c in claim)
    if chinese>len(claim)*0.2:raise ValueError('SOURCE_LANGUAGE_NOT_SELECTED')
    exact=bool(re.search(r'(?<![1-9A-HJ-NP-Za-km-z])'+re.escape(mint)+r'(?![1-9A-HJ-NP-Za-km-z])',combined))
    published=None
    candidate=parser.meta.get('article:published_time') or parser.meta.get('datepublished')
    if candidate:
        try:
            dt=datetime.fromisoformat(candidate.replace('Z','+00:00'))
            if dt.tzinfo is not None:published=dt.astimezone(timezone.utc).isoformat()
        except (ValueError,OverflowError):pass
    story=story_fields(combined,parser.links)
    normalized={'title':' '.join(title.split()),'description':' '.join(description.split()),
                'author':' '.join(str(parser.meta.get('author') or '').split()),'published_at_claim':published,
                'text':' '.join(text.split()),'post_links':story['post_links']}
    return {'classification':'THIRD_PARTY_CLAIM','source_url':url,'publisher_host':urlsplit(url).hostname,
            'title':clip(title,6,80),'author_claim':clip(parser.meta.get('author'),2,60) or None,
            'excerpt':story_excerpt(description,text),'exact_ca_mentioned':exact,'url_contains_ca':mint in url,
            'story':story,'content_sha256':hashlib.sha256(json.dumps(normalized,sort_keys=True).encode()).hexdigest(),
            'official_recognition':'UNVERIFIED','published_at_claim':published,'first_seen_at':observed_at,
            'first_seen_scope':'THIS_REPORT_ONLY','text_scope':'STATIC_HTML_TEXT_OR_DESCRIPTION; NO_RENDERED_VISIBILITY_CHECK',
            'response_sha256':hashlib.sha256(raw).hexdigest()}


FETCH_REASONS = frozenset({
    'URL_NOT_ALLOWED','DNS_NOT_PUBLIC','PUBLIC_IPV4_UNAVAILABLE','DNS_UNAVAILABLE',
    'REDIRECT_NOT_FOLLOWED','NOT_HTML','NOT_JSON','COMPRESSED_BODY_NOT_SUPPORTED','RESPONSE_LIMIT',
    'SOURCE_UNAVAILABLE','FETCH_WORKER_FAILED','FETCH_TIMEOUT','TimeoutError',
})
CLAIM_REASONS = frozenset({
    'RESPONSE_LIMIT','RESPONSE_TEXT_INVALID','ACCESS_WALL_OR_SCRIPT_ONLY',
    'NO_EXTRACTABLE_CLAIM','SOURCE_LANGUAGE_NOT_SELECTED',
})


def _source_reason(value):
    if isinstance(value,str) and (value in FETCH_REASONS or re.fullmatch(r'HTTP_[0-9]{3}',value)):
        return value
    return 'SOURCE_UNAVAILABLE'


def _social_urls(market):
    rows=market.get('socials') if isinstance(market,dict) else None
    for row in rows if isinstance(rows,list) else ():
        if not isinstance(row,dict):continue
        url,handle=row.get('url'),row.get('handle')
        if not url and isinstance(handle,str):
            if handle.startswith('https://'):url=handle
            elif str(row.get('platform') or '').lower() in {'x','twitter'} and re.fullmatch(r'@?[A-Za-z0-9_]{1,30}',handle):
                url='https://x.com/'+handle.lstrip('@')
        if isinstance(url,str):yield url


def _read_claim(fetch,clock,kind,url,mint):
    claim=None
    attempt={'kind':kind,'source_url':url,'requested':True,'status':'UNAVAILABLE'}
    try:
        result=fetch(url)
        reason=_source_reason(result.get('reason'))
        if result.get('status')=='OK':
            encoded=result.get('body_b64','')
            if not isinstance(encoded,str) or len(encoded)>2*MAX_HTML_BYTES:raise ValueError('RESPONSE_LIMIT')
            claim=extract_page_claim(base64.b64decode(encoded,validate=True),url,mint,clock())
            claim['source_kind']=kind
            attempt.update(status='CLAIM_READ',response_sha256=claim['response_sha256'])
            reason=None
    except (ValueError,TypeError,KeyError,AttributeError,OSError) as exc:
        reason=str(exc) if str(exc) in CLAIM_REASONS else 'SOURCE_UNAVAILABLE'
    attempt.update(observed_at=clock(),reason=reason)
    return attempt,claim


class PublicNarrativeClient:
    def __init__(self,*,fetch=read_public_html,clock=time.time,fetch_json=None):self.fetch=fetch;self.clock=clock;self.fetch_json=fetch_json

    def collect_origin(self,mint,metadata,market):
        return collect_origin(mint,metadata,market,fetch_json=self.fetch_json or read_public_json,
                              fetch_html=self.fetch,clock=self.clock)

    def collect(self,mint,market):
        attempts=[];evidence=[];seen=set();claim_keys=set()
        out={'version':1,'status':'UNAVAILABLE','attempts':attempts,'evidence':evidence,
             'official_recognition':'UNVERIFIED','exhaustive':False,'search_coverage':'BOUNDED_HINTS_ONLY',
             'recursive_crawl':False,'earliest_origin':'UNVERIFIED'}
        if not valid_pubkey(mint):return {**out,'reason':'MINT_IDENTITY_UNVERIFIED'}
        websites=market.get('websites') if isinstance(market,dict) else None
        candidates=[('LAUNCHPAD_PAGE','https://pump.fun/coin/'+mint)]
        if isinstance(websites,list):
            candidates.extend(('MARKET_WEBSITE_HINT',url) for url in websites if isinstance(url,str))
        candidates.extend(('MARKET_SOCIAL_HINT',url) for url in _social_urls(market))
        for kind,hint in candidates:
            try:url=canonical_url(hint)
            except ValueError:
                attempts.append({'kind':kind,'status':'UNAVAILABLE','reason':'URL_NOT_ALLOWED','requested':False});continue
            if url in seen:continue
            seen.add(url)
            attempt,claim=_read_claim(self.fetch,self.clock,kind,url,mint)
            if claim:
                fingerprint=claim['content_sha256']
                if fingerprint in claim_keys:
                    attempt.update(status='DUPLICATE_CONTENT',reason='DUPLICATE_CONTENT')
                else:
                    claim_keys.add(fingerprint);evidence.append(claim)
            attempts.append(attempt)
        return {**out,'status':'PARTIAL' if evidence else 'UNAVAILABLE','story_summary':story_summary(evidence)}


IPFS_GATEWAYS=('https://{cid}.ipfs.4everland.io/{path}','https://ipfs.filebase.io/ipfs/{cid}/{path}','https://gateway.pinata.cloud/ipfs/{cid}/{path}')
STATUS_RE=re.compile(r'^https://(?:www\.)?(?:x|twitter)\.com/([A-Za-z0-9_]{1,30})/status/([0-9]{5,25})/?$')
HANDLE_RE=re.compile(r'[A-Za-z0-9_]{1,30}')
POST_ID_RE=re.compile(r'[0-9]{5,25}')
HASH_RE=re.compile(r'[a-f0-9]{64}')


def ipfs_candidates(uri):
    if not isinstance(uri,str) or len(uri)>512:return []
    uri=uri.strip()
    m=re.match(r'^(?:ipfs://(?:ipfs/)?|https://[^/]+/ipfs/)([A-Za-z0-9]{46,100})(/[^?#]*)?$',uri) or re.match(r'^https://([a-z0-9]{46,100})\.ipfs\.[a-z0-9.-]+(/[^?#]*)?$',uri)
    if not m:return [uri] if uri.startswith('https://') else []
    cid=m.group(1);path=(m.group(2) or '/').lstrip('/')
    return [g.format(cid=cid.lower() if g.startswith('https://{cid}') else cid,path=path).rstrip('/') or g for g in IPFS_GATEWAYS]


def _short(value,n):return ' '.join(str(value or '').split())[:n]


def _post_ref(url):
    try:match=STATUS_RE.fullmatch(canonical_url(url))
    except ValueError:return None
    return (match[1].lower(),match[2]) if match else None


def _post_url(ref):
    return f'https://x.com/{ref[0]}/status/{ref[1]}'


def _exact(text,mint):
    return bool(re.search(r'(?<![1-9A-HJ-NP-Za-km-z])'+re.escape(mint)+r'(?![1-9A-HJ-NP-Za-km-z])',str(text or '')))


def _response_hash(value):
    return value if isinstance(value,str) and HASH_RE.fullmatch(value) else None


def _source_number(value):
    return value if type(value) is int and value>=0 else None


def _timestamp(value):
    return value if type(value) is int and 0<value<4102444800 else None


def _post(raw,post_id,mint,response_hash):
    """Bind an existing FxTwitter response to a post id and its reported author."""
    if (not isinstance(raw,dict) or raw.get('id')!=post_id or raw.get('provider','twitter')!='twitter'
            or not response_hash):
        return None
    author=raw.get('author')
    if not isinstance(author,dict):return None
    handle=author.get('screen_name')
    if not isinstance(handle,str) or not HANDLE_RE.fullmatch(handle):return None
    author_ref=(handle.lower(),post_id)
    if _post_ref(raw.get('url'))!=author_ref:return None
    author_id=author.get('id')
    if not isinstance(author_id,str) or not author_id.isascii() or not author_id.isdigit():
        author_id=None
    verification=author.get('verification')
    ver=verification if isinstance(verification,dict) else {}
    text=raw.get('text') if isinstance(raw.get('text'),str) else ''
    actors=[name for name,pattern in ACTORS if re.search(pattern,text+' @'+handle,re.I)]
    return {'url':_post_url(author_ref),'id':post_id,'author':handle,'author_id':author_id,
            'author_name':_short(author.get('name'),60),'author_followers':_source_number(author.get('followers')),
            'author_verified':ver.get('verified') is True,'created_at':_timestamp(raw.get('created_timestamp')),
            'text':_short(text,600),'response_sha256':response_hash,
            'likes':_source_number(raw.get('likes')),'reposts':_source_number(raw.get('retweets')),
            'quotes':_source_number(raw.get('quotes')),'views':_source_number(raw.get('views')),
            'exact_ca_mentioned':_exact(text,mint),'actors_in_text_or_author':actors}


def _post_targets(tweet):
    quoted=tweet.get('quote')
    quote_ref=_post_ref(quoted.get('url')) if isinstance(quoted,dict) else None
    if quote_ref and quoted.get('id',quote_ref[1])==quote_ref[1]:
        yield 'QUOTE',quote_ref
    handle,post_id=tweet.get('replying_to'),tweet.get('replying_to_status')
    if (isinstance(handle,str) and HANDLE_RE.fullmatch(handle)
            and isinstance(post_id,str) and POST_ID_RE.fullmatch(post_id)):
        yield 'REPLY',(handle.lower(),post_id)


def _explicit_claim(tweet,mint):
    # Check the author's original full text. An exact address in a quotation,
    # a repost, a negation, or descriptive prose cannot certify a claim.
    text=tweet.get('text')
    if not isinstance(text,str) or tweet.get('reposted_by'):return False
    pattern=r'(?i:our official (?:solana )?(?:ca|contract address|mint)(?:\s+is\s+|\s*:\s*))'+re.escape(mint)+r'\.?'
    return re.fullmatch(pattern,text.strip()) is not None


def collect_origin(mint,metadata,market,*,fetch_json=read_public_json,fetch_html=read_public_html,clock=time.time):
    """Follow observed post references with a single read per id and preserve every edge."""
    out={'version':1,'status':'UNAVAILABLE','reads':[],'creator_metadata':None,'creator_website_evidence':None,
         'posts':[],'interactions':[],'unresolved_links':[],'ca_link_status':'UNVERIFIED',
         'recognition':{'status':'SOURCE_UNAVAILABLE','mint':mint},
         'earliest_traceable':None,'earliest_scope':'QUOTE_AND_REPLY_CHAIN_FROM_LINKED_POST_NOT_EXHAUSTIVE',
         'observed_at':clock(),'exhaustive':False}
    if not valid_pubkey(mint):
        return {**out,'reason':'MINT_IDENTITY_UNVERIFIED'}

    def read(kind,url):
        row={'kind':kind,'status':'UNAVAILABLE','requested':False}
        try:url=canonical_url(url)
        except ValueError:row['reason']='URL_NOT_ALLOWED'
        else:
            row.update(url=url,requested=True)
            try:result=fetch_json(url)
            except RPCJobBudgetExceeded:raise
            except Exception as exc:result={'status':'UNAVAILABLE','reason':type(exc).__name__}
            if not isinstance(result,dict):result={}
            status='OK' if result.get('status')=='OK' else 'UNAVAILABLE'
            row.update(status=status,reason=None if status=='OK' else _source_reason(result.get('reason')),
                       response_sha256=_response_hash(result.get('response_sha256')))
        out['reads'].append(row)
        return row,result.get('json') if row['status']=='OK' else None

    meta=None
    meta_read=None
    if isinstance(metadata,dict) and metadata.get('status')=='VERIFIED_CHAIN_STATE' and metadata.get('mint')==mint:
        for url in ipfs_candidates(metadata.get('uri')):
            item,value=read('CREATOR_METADATA_JSON',url)
            if isinstance(value,dict):meta=value;meta_read=item;break
            if item['status']=='OK':item.update(status='UNAVAILABLE',reason='NOT_JSON_OBJECT')

    queue=deque()
    creator_post=None
    page_links=market.get('narrative_post_links') if isinstance(market,dict) else None
    if isinstance(meta,dict):
        links={}
        for key in ('twitter','website','telegram','createdOn'):
            if key not in meta:continue
            try:links[key]=canonical_url(meta[key])
            except ValueError:out['unresolved_links'].append({'kind':'CREATOR_METADATA_'+key.upper(),'reason':'URL_NOT_ALLOWED'})
        out['creator_metadata']={'uri':meta_read['url'],'source':metadata.get('source'),
            'name':_short(meta.get('name'),64),'symbol':_short(meta.get('symbol'),32),'description':_short(meta.get('description'),400),
            'links':links,'name_matches_chain':_short(meta.get('name'),64)==_short(metadata.get('name'),64),
            'symbol_matches_chain':_short(meta.get('symbol'),32)==_short(metadata.get('symbol'),32),
            'metadata_mutable':metadata.get('is_mutable'),'response_sha256':meta_read['response_sha256'],
            'scope':'URI_COMMITTED_ON_CHAIN_FOR_THIS_MINT; OFFCHAIN_CONTENT_AUTHOR_UNVERIFIED'}
        if links.get('twitter'):
            creator_post=_post_ref(links['twitter'])
            if creator_post:
                queue.append((creator_post,'LINKED_BY_CREATOR_METADATA',None))
                out['ca_link_status']='CREATOR_METADATA_LINKS_POST'
            else:
                out['unresolved_links'].append({'kind':'CREATOR_METADATA_TWITTER','url':links['twitter'],
                                                'reason':'PROFILE_OR_NON_POST_LINK'})
        already_read=market.get('narrative_read_urls') if isinstance(market,dict) else None
        if links.get('website') and links['website'] not in (already_read if isinstance(already_read,list) else []):
            attempt,claim=_read_claim(fetch_html,clock,'CREATOR_METADATA_WEBSITE',links['website'],mint)
            out['reads'].append({**attempt,'url':attempt['source_url']})
            out['creator_website_evidence']=claim
            if claim:
                page_links=[*(page_links if isinstance(page_links,list) else []),*claim['story']['post_links']]
    for url in _social_urls(market):
        ref=_post_ref(url)
        if ref:queue.append((ref,'LINKED_BY_MARKET_SOCIAL',None))
    for url in page_links if isinstance(page_links,list) else ():
        ref=_post_ref(url)
        if ref:queue.append((ref,'LINKED_BY_READ_PAGE',None))

    seen_edges=set()
    responses={}
    posts={}
    while queue:
        ref,relation,source_id=queue.popleft()
        edge=(ref,relation,source_id)
        if edge in seen_edges:continue
        seen_edges.add(edge)
        post_id=ref[1]
        if post_id not in responses:
            row,data=read('X_POST_API',f'https://api.fxtwitter.com/{ref[0]}/status/{post_id}')
            tweet=data.get('tweet') if isinstance(data,dict) else None
            post=_post(tweet,post_id,mint,row.get('response_sha256'))
            if post is None and row['status']=='OK':
                row.update(status='UNAVAILABLE',reason='POST_IDENTITY_UNVERIFIED')
            responses[post_id]=row,tweet,post
        row,tweet,post=responses[post_id]
        from_post=posts.get(source_id)
        if post is None or post['author'].lower()!=ref[0]:
            out['unresolved_links'].append({'kind':relation,'url':_post_url(ref),
                'from':from_post['url'] if from_post else None,
                'reason':row['reason'] if post is None else 'POST_LINK_AUTHOR_MISMATCH'})
            continue
        if post_id not in posts:
            post.update(relation=relation)
            if from_post:post['quoted_by']=from_post['url']
            posts[post_id]=post
            out['posts'].append(post)
            for interaction,related in _post_targets(tweet):
                queue.append((related,interaction,post_id))
        if from_post:
            out['interactions'].append({'from':from_post['url'],'to':post['url'],'author':from_post['author'],
                'author_id':from_post['author_id'],'target_author':post['author'],'type':relation,
                'status':'API_REPORTED_STRUCTURAL_RELATION'})

    linked=next((post for post in out['posts'] if post['relation'].startswith('LINKED_BY_')),None)
    pair=market.get('main_pair') if isinstance(market,dict) else None
    pair_ms=_source_number(pair.get('pair_created_at_ms')) if isinstance(pair,dict) else None
    if linked and linked['created_at'] is not None and pair_ms:
        out['linked_post_to_pair_seconds']=round(pair_ms/1000-linked['created_at'],1)
    if any(p['exact_ca_mentioned'] for p in out['posts']):
        out['ca_link_status']='POST_MENTIONS_EXACT_CA'
    dated=[p for p in out['posts'] if p['created_at'] is not None]
    if dated:
        first=min(dated,key=lambda p:(p['created_at'],int(p['id'])))
        out['earliest_traceable']={key:first[key] for key in ('url','author','created_at','relation','response_sha256')}

    creator=out['creator_metadata']
    issuer=next((post for post in out['posts'] if post['relation']=='LINKED_BY_CREATOR_METADATA'),None)
    if (issuer and creator['response_sha256'] and issuer['response_sha256']
            and issuer['author_id'] and _explicit_claim(responses[issuer['id']][1],mint)):
        out['recognition'].update(status='EXACT_CA_CLAIM_VERIFIED',basis='CHAIN_LINKED_POST_AUTHOR_EXPLICIT_EXACT_MINT_CLAIM',
            source_url=issuer['url'],author=issuer['author'],author_id=issuer['author_id'],
            post_response_sha256=issuer['response_sha256'],metadata_response_sha256=creator['response_sha256'])
    elif creator and creator['links']:
        out['recognition'].update(status='LINK_ONLY',basis='CHAIN_METADATA_URI_EXTERNAL_LINK_ONLY')
    elif out['posts'] or creator or (isinstance(market,dict) and market.get('narrative_claims_read')):
        out['recognition'].update(status='NO_VERIFIABLE_CLAIM')
    out['status']='PARTIAL' if (creator or out['posts']) else 'UNAVAILABLE'
    return out
