"""Bounded public source claims, distinct from official exact-CA recognition."""
import base64
from datetime import datetime,timezone
import hashlib
import json
from html.parser import HTMLParser
import re
import time
from urllib.parse import urlsplit
from .holder_ranks import valid_pubkey
from .public_html import canonical_url,read_public_html,MAX_HTML_BYTES


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
        if len(posts)==4:break
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
        if tag=='a' and len(self.links)<64 and isinstance(attrs.get('href'),str):self.links.append(attrs['href'])
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


class PublicNarrativeClient:
    def __init__(self,*,fetch=read_public_html,clock=time.time):self.fetch=fetch;self.clock=clock
    def collect(self,mint,market):
        if not valid_pubkey(mint):return {'version':1,'status':'UNAVAILABLE','attempts':[],'evidence':[],'reason':'MINT_IDENTITY_UNVERIFIED','official_recognition':'UNVERIFIED','exhaustive':False,'search_coverage':'BOUNDED_HINTS_ONLY'}
        websites=[v for v in (market.get('websites') or [])[:4] if isinstance(v,str)]
        socials=[]
        for row in (market.get('socials') or [])[:2]:
            if not isinstance(row,dict):continue
            url=row.get('url');handle=row.get('handle')
            if not url and isinstance(handle,str):
                if handle.startswith('https://'):url=handle
                elif str(row.get('platform') or '').lower() in {'x','twitter'} and re.fullmatch(r'@?[A-Za-z0-9_]{1,30}',handle):url='https://x.com/'+handle.lstrip('@')
            if isinstance(url,str):socials.append(url)
        candidates=[('LAUNCHPAD_PAGE','https://pump.fun/coin/'+mint)]
        candidates += [('MARKET_WEBSITE_HINT',v) for v in websites[:1]]
        candidates += [('MARKET_SOCIAL_HINT',v) for v in socials[:1]]
        candidates += [('MARKET_WEBSITE_HINT',v) for v in websites[1:]]
        candidates += [('MARKET_SOCIAL_HINT',v) for v in socials[1:]]
        attempts=[];evidence=[];seen=set();claim_keys=set();reads=0
        for kind,hint in candidates:
            try:url=canonical_url(hint)
            except ValueError:
                attempts.append({'kind':kind,'status':'UNAVAILABLE','reason':'URL_NOT_ALLOWED','requested':False});continue
            if url in seen:continue
            seen.add(url)
            if reads>=3:
                attempts.append({'kind':kind,'source_url':url,'status':'NOT_REQUESTED','reason':'SOURCE_LIMIT','requested':False});continue
            reads+=1;when=self.clock()
            attempt={'kind':kind,'source_url':url,'observed_at':when,'requested':True}
            try:
                result=self.fetch(url)
                when=self.clock();attempt['observed_at']=when
                if result.get('status')!='OK':
                    reason=result.get('reason','SOURCE_UNAVAILABLE')
                    allowed={'URL_NOT_ALLOWED','DNS_NOT_PUBLIC','PUBLIC_IPV4_UNAVAILABLE','DNS_UNAVAILABLE','REDIRECT_NOT_FOLLOWED','NOT_HTML','COMPRESSED_BODY_NOT_SUPPORTED','RESPONSE_LIMIT','SOURCE_UNAVAILABLE','FETCH_WORKER_FAILED','FETCH_TIMEOUT'}
                    if reason not in allowed and not re.fullmatch(r'HTTP_[0-9]{3}',str(reason)):reason='SOURCE_UNAVAILABLE'
                    attempt.update(status='UNAVAILABLE',reason=reason)
                else:
                    encoded=result.get('body_b64','')
                    if not isinstance(encoded,str) or len(encoded)>2*MAX_HTML_BYTES:raise ValueError('RESPONSE_LIMIT')
                    raw=base64.b64decode(encoded,validate=True)
                    claim=extract_page_claim(raw,url,mint,when);claim['source_kind']=kind
                    fingerprint=claim['content_sha256']
                    if fingerprint in claim_keys:attempt.update(status='DUPLICATE_CONTENT',reason='DUPLICATE_CONTENT')
                    else:
                        claim_keys.add(fingerprint);evidence.append(claim);attempt.update(status='CLAIM_READ',reason=None)
            except (ValueError,TypeError,KeyError,AttributeError,OSError) as exc:
                reason=str(exc) if str(exc) in {'RESPONSE_LIMIT','RESPONSE_TEXT_INVALID','ACCESS_WALL_OR_SCRIPT_ONLY','NO_EXTRACTABLE_CLAIM','SOURCE_LANGUAGE_NOT_SELECTED'} else 'SOURCE_UNAVAILABLE'
                attempt.update(status='UNAVAILABLE',reason=reason)
            attempts.append(attempt)
        return {'version':1,'status':'PARTIAL' if evidence else 'UNAVAILABLE','attempts':attempts,'evidence':evidence,
                'official_recognition':'UNVERIFIED','exhaustive':False,'search_coverage':'BOUNDED_HINTS_ONLY',
                'source_request_limit':3,'recursive_crawl':False,'earliest_origin':'UNVERIFIED',
                'story_summary':story_summary(evidence)}
