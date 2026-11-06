"""Narrative usefulness and evidence boundaries; synthetic page bytes only."""
import base64
import hashlib
from html import escape
import re

import pytest

from mission_agent.meme.narrative import PublicNarrativeClient, extract_page_claim
from test_meme_holder_ranks import MINT


URL = 'https://project.example.org/story'
POST = 'https://x.com/elonmusk/status/1234567890123456789'


def page(description='', body='', title='A source story', author='Project Team'):
    return (
        '<html lang="en"><head><title>' + escape(title) + '</title>'
        '<meta name="author" content="' + escape(author, quote=True) + '">'
        '<meta name="description" content="' + escape(description, quote=True) + '">'
        '</head><body>' + body + '</body></html>'
    ).encode()


def response(raw):
    return {'status': 'OK', 'body_b64': base64.b64encode(raw).decode()}


def collect_pages(pages, websites=None):
    calls = []

    def fetch(url):
        calls.append(url)
        if url not in pages:
            return {'status': 'UNAVAILABLE', 'reason': 'HTTP_403'}
        return response(pages[url])

    report = PublicNarrativeClient(fetch=fetch, clock=lambda: 100).collect(
        MINT, {'websites': websites or list(pages), 'socials': []})
    return report, calls


def test_concrete_body_event_survives_generic_description_without_verifying_it():
    raw = page(
        description='A community meme token about imaginary cats and distant planets.',
        body='<article>Elon Musk replied to this artist. '
             '<a href="' + POST + '">Source post</a></article>')
    claim = extract_page_claim(raw, URL, MINT, 100)

    assert 'Elon Musk replied to this artist.' in claim['excerpt']
    assert claim['story']['actors_mentioned'] == ['ELON_MUSK']
    assert claim['story']['interaction_status'] == 'UNVERIFIED'
    assert claim['story']['post_links'] == [POST]
    assert claim['official_recognition'] == 'UNVERIFIED'
    assert claim['exact_ca_mentioned'] is False
    assert claim['response_sha256'] == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize('statement', [
    'Elon Musk replied to this artist.',
    'The project claims Elon Musk replied to its artist.',
    'Elon Musk did not endorse this token or its contract.',
    'The token name borrows Elon Musk without evidence of his participation.',
])
def test_actor_mention_claim_negation_and_name_borrowing_never_verify_interaction(statement):
    claim = extract_page_claim(page(body='<p>' + statement + '</p>'), URL, MINT, 100)
    assert 'ELON_MUSK' in claim['story']['actors_mentioned']
    assert claim['story']['interaction_status'] == 'UNVERIFIED'
    assert claim['official_recognition'] == 'UNVERIFIED'
    assert claim['classification'] == 'THIRD_PARTY_CLAIM'


def test_complete_short_sentence_is_displayed_instead_of_a_long_mid_sentence_fragment():
    first = 'A crawler trains an AI model.'
    description = first + ' It visits public websites and reads many pages with enough extra words to exceed the short excerpt budget.'
    claim = extract_page_claim(page(description=description), URL, MINT, 100)
    assert claim['excerpt'] == first
    assert len(claim['excerpt'].split()) <= 16
    assert len(claim['title'].split()) <= 6
    assert len(claim['author_claim'].split()) <= 2


def test_distinct_claims_with_the_same_display_prefix_are_not_false_duplicates():
    prefix = 'One two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen '
    url2 = 'https://second.example.org/story'
    raw1 = page(body=prefix + 'This token celebrates the artists original work.')
    raw2 = page(body=prefix + 'This token has no connection with that artist.')
    first = extract_page_claim(raw1, URL, MINT, 100)
    second = extract_page_claim(raw2, url2, MINT, 100)
    assert first['excerpt'] == second['excerpt']
    assert re.fullmatch('[a-f0-9]{64}', first['content_sha256'])
    assert first['content_sha256'] != second['content_sha256']

    report, calls = collect_pages({URL: raw1, url2: raw2})
    assert len(calls) == 3
    assert len(report['evidence']) == 2
    assert not any(row['status'] == 'DUPLICATE_CONTENT' for row in report['attempts'])


def test_true_mirrors_still_count_as_one_claim_despite_different_source_urls():
    url2 = 'https://mirror.example.org/story'
    raw = page(description='A crawler reads public websites to train a crypto native AI model.')
    report, calls = collect_pages({URL: raw, url2: raw})
    assert len(calls) == 3
    assert len(report['evidence']) == 1
    assert sum(row['status'] == 'DUPLICATE_CONTENT' for row in report['attempts']) == 1
    assert report['official_recognition'] == 'UNVERIFIED'


def test_different_claimed_authors_do_not_disappear_as_mirrors():
    first=extract_page_claim(page(description='A crawler trains an AI model.',author='Original Artist'),URL,MINT,100)
    second=extract_page_claim(page(description='A crawler trains an AI model.',author='Another Publisher'),URL,MINT,100)
    assert first['content_sha256'] != second['content_sha256']


def test_long_source_sentence_is_explicitly_an_excerpt():
    text='A crawler trains models using public data and this single long sentence continues beyond the bounded source excerpt words.'
    claim=extract_page_claim(page(description=text),URL,MINT,100)
    assert claim['excerpt'].endswith('…') and len(claim['excerpt'].split())<=16


@pytest.mark.parametrize('text',[
    'This wildlife token celebrates the endangered musk deer in Asian forests.',
    'A trick taking card game where the trump card beats other suits.',
])
def test_ambiguous_common_words_do_not_invent_person_mentions(text):
    claim=extract_page_claim(page(description=text),URL,MINT,100)
    assert claim['story']['actors_mentioned']==[]
    assert '人物／事件关联说法' not in claim['story']['themes']


def test_closing_hidden_ancestor_preserves_following_visible_story_with_omitted_p_end():
    raw=page(description='A fictional cat community lives on another planet.',
             body='<div hidden><p>Secret unrelated material.</div><p>Elon Musk replied to the original artist.</p>')
    claim=extract_page_claim(raw,URL,MINT,100)
    assert claim['excerpt']=='Elon Musk replied to the original artist.'
    assert claim['story']['actors_mentioned']==['ELON_MUSK']
    assert claim['story']['interaction_status']=='UNVERIFIED'


@pytest.mark.parametrize('unsafe', [
    'http://x.com/elonmusk/status/1234567890123456789',
    'https://127.0.0.1/elonmusk/status/1234567890123456789',
    'https://x.com.attacker.example/elonmusk/status/1234567890123456789',
    'https://user:secret@x.com/elonmusk/status/1234567890123456789',
    'https://x.com/elonmusk/status/1234567890123456789?key=SECRET',
    'javascript:alert(1)',
    '/elonmusk/status/1234567890123456789',
    'https://x.com/elonmusk',
])
def test_unsafe_or_non_post_anchor_is_not_treated_as_interaction_evidence(unsafe):
    claim = extract_page_claim(page(body=(
        '<p>This community describes a fictional animal and an unverified story.</p>'
        '<a href="' + escape(unsafe, quote=True) + '">Claim source</a>')), URL, MINT, 100)
    assert claim['story']['post_links'] == []
    assert claim['story']['interaction_status'] == 'UNVERIFIED'
    assert 'SECRET' not in str(claim)


def test_post_links_in_scripts_templates_and_hidden_anchors_are_not_extracted():
    hidden = '<a href="' + POST + '">Hidden claim</a>'
    claim = extract_page_claim(page(body=(
        '<p>A community story about a fictional animal exploring distant planets.</p>'
        '<script>"' + hidden + '"</script>'
        '<template>' + hidden + '</template>'
        '<div hidden>' + hidden + '</div>'
        '<div aria-hidden="true">' + hidden + '</div>')), URL, MINT, 100)
    assert claim['story']['post_links'] == []
    assert claim['story']['actors_mentioned'] == []


def test_visible_original_post_links_are_retained_once_but_never_fetched():
    twitter = 'https://twitter.com/artist/status/1234567890123456790'
    raw = page(body=(
        '<p>The project claims an interaction and links public posts for review.</p>'
        '<a href="' + POST + '">Original</a>'
        '<a href="' + POST + '">Repeated</a>'
        '<a href="' + twitter + '">Other post</a>'))
    report, calls = collect_pages({URL: raw})
    claim = report['evidence'][0]
    assert set(claim['story']['post_links']) == {POST, twitter}
    assert len(claim['story']['post_links']) == 2
    assert calls == ['https://pump.fun/coin/' + MINT, URL]
    assert claim['story']['interaction_status'] == 'UNVERIFIED'
    assert report['recursive_crawl'] is False


def test_story_remains_available_without_ca_recognition_and_theme_is_source_derived():
    raw = page(description='An AI crawler reads public websites to train a crypto native language model.')
    report, _ = collect_pages({URL: raw})
    claim = report['evidence'][0]
    summary = report['story_summary']
    assert claim['exact_ca_mentioned'] is False
    assert summary['version'] == 1 and summary['status'] == 'SOURCE_CLAIMS'
    assert summary['sources_read'] == 1
    assert summary['themes'] and all(isinstance(item, str) for item in summary['themes'])
    assert set(summary['themes']) == set(claim['story']['themes'])
    assert summary['interaction_status'] == summary['official_recognition'] == 'UNVERIFIED'
    assert claim['story']['actors_mentioned'] == []


def test_failed_sources_report_no_story_instead_of_inventing_a_topic():
    report, calls = collect_pages({}, websites=[URL])
    summary = report['story_summary']
    assert len(calls) == 2 and report['evidence'] == []
    assert summary['status'] == 'UNAVAILABLE'
    assert summary['sources_read'] == 0 and summary['themes'] == []
    assert summary['interaction_status'] == summary['official_recognition'] == 'UNVERIFIED'


def test_story_collection_keeps_three_requests_and_does_not_follow_post_links():
    pages = {url: page(description='A fictional community story from ' + url,
                       body='<a href="' + POST + '">Original post</a>')
             for url in [URL, 'https://second.example.org/', 'https://third.example.org/']}
    report, calls = collect_pages(pages)
    assert len(calls) == 3
    assert POST not in calls
    assert report['source_request_limit'] == 3 and report['recursive_crawl'] is False
    assert any(row['reason'] == 'SOURCE_LIMIT' and row['requested'] is False
               for row in report['attempts'])
