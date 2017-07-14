import ast
import sqlite3
import json
import re
import numpy as np
import pickle
from collections import defaultdict
from exceptions import IndentationError
from HTMLParser import HTMLParser
from tokenize import generate_tokens
from cStringIO import StringIO
from astor import to_source

from normalization import normalize_code


sqlite_file = 'store.db'
conn = sqlite3.connect(sqlite_file)

def query(sql):
    return conn.cursor().execute(sql).fetchall()


#get title for all posts
titles = {post_id: title for post_id, title in query('select id, title from post where title is not null')}
pickle.dump(titles, open('titles.p', 'wb'))


#get the postid of accepted answer for all posts
accepted_posts = {post_id: accepted_answer_id for post_id, accepted_answer_id in query('select id, accepted_answer_id from post where accepted_answer_id is not null')}


#get html_body for all posts
posts = {post_id: body for post_id, body in query('select id, body from post')}
pickle.dump(posts, open('posts.p', 'wb'))


#get question id and voting score for all answer posts
#questins: list((answer_post_score, answer_post_id))
question_answer_scores = defaultdict(list)
for post_id, parent_id, score in query('select id, parent_id, score from post where parent_id is not null'):
    question_answer_scores[parent_id].append((score, post_id))


#get all the user annotations (saved in json format), note that for one post there maybe multiple annotations
annotations = [(post_id, json.loads(annotation_json)) for post_id, annotation_json in query('select post_id, annotation_json from annotation')]


#filter out all the annotations which were marked as not_sure
confident_annotations = [(post_id, annotation) for post_id, annotation in annotations if not annotation['notSure']]


#since we only considered the top 3 answers, but in the database, we stored all the
#answers for a post, here we just extract all the answer_id which were showed to user
annotated_questions = {}
for post_id, annotation in confident_annotations:
    annotated_questions[post_id] = set(sorted(question_answer_scores[post_id], key=lambda x:-x[0])[:3])


#get char-based offsets i.e (start_of_code_snippet, end_of_code_snippet) for all
#the code snippets inside a html body (post content)
def get_code_span(html, match):
    start, end = match.span()
    code = match.group(1)
    start += html[start:end].find(code)
    end = start + len(code)
    return (start, end)


def get_code_spans(html, is_code):
    if not is_code:
        return [(0, len(html))]
    matches = re.finditer(r"<pre[^>]*>[^<]*<code[^>]*>((?:\s|[^<]|<span[^>]*>[^<]+</span>)*)</code></pre>", html)
    return [get_code_span(html, m) for m in matches]


#get all the offsets of code selected by user, since the user selection might
#include html tag or some content outside <code> tag. Here we just take the
#intersections of code_snippets and user_selection
def merge_spans(html, code_spans, sel_spans):
    masks = np.zeros(len(html))
    for start, end in code_spans:
        masks[start:end] += 1.
    for start, end in sel_spans:
        masks[start:end] += 1.
    masks = masks == 2
    for i in range(1, len(html)):
        if html[i].isspace() and masks[i - 1]:
            masks[i] = True
    for i in reversed(range(len(html) - 2)):
        if html[i].isspace() and masks[i + 1]:
            masks[i] = True
    for start, end in code_spans:
        code = [c for c, m in zip(html[start:end], masks[start:end]) if m]
        if len(code) > 0:
            yield ''.join(code)


#parse selection ranges to (html_text, start_offset, end_offset)
def parse_range(post_id, selected_range, is_code):
    source, source_id = selected_range['source'].split('-')
    source_id = int(source_id)
    if source == 'title':
        text = titles[source_id]
    else:
        text = posts[source_id]
    start, end = selected_range['start'], selected_range['end']
    return text, start, end


#parse annotation selection as (html_text, parsed_selected_text, saved_reference_text)
#when user annotated a post, saved_reference_text was saved from browser, which is the
#text selected by user (without any html tag), however, the user might mis-selected some
#text outside tht code-snippet, we only use it as an reference for sanity check, the ground
#truth is generated by parse_range
def parse_selection(post_id, selection, is_code):
    ref_text = selection['html']
    sel_spans = []
    source_text = None
    for selected_range in selection['pos']:
        text, start, end = parse_range(post_id, selected_range, is_code)
        if source_text is None:
            source_text = text
        else:
            assert source_text == text
        sel_spans.append((start, end))
    sel_text = '\n'.join(merge_spans(source_text, get_code_spans(source_text, is_code), sel_spans))
    return source_text, sel_text, re.sub('<[^<]+?>', '', ref_text.strip())


#parse multiple selection of a post as an array of (html_text, parsed_selected_text, saved_reference_text)
def parse_selections(post_id, selections, is_code=True):
    if selections is None:
        return []
    return [parse_selection(post_id, s, is_code) for s in selections]


#parse annotation record
def parse_annotation(post_id, annotation):
    return {
        'post_id': post_id,
        'intent': parse_selections(post_id, annotation['question'], is_code=False),
        'context': parse_selections(post_id, annotation['context']),
        'snippet': parse_selections(post_id, annotation['snippet']),
    }


#get all the confident annotation results
parsed_confident_annotations = [parse_annotation(post_id, a) for post_id, a in confident_annotations]


#unescape the html context (e.g. &amp => &)
def unescape(text, parser=HTMLParser()):
    return parser.unescape(text)


#get all the code snippet form a html context (extracting all the sub-text inside <code> tags)
#for future snippet-candidates generation
def get_code_list(html_list, is_code=True):
    for html in html_list:
        for start, end in get_code_spans(html, is_code):
            yield unescape(html[start:end])


#parse all the annotation record in to a dict format, (*_ref ground truth), (*_text meta candidate)
# post_id: question id
# intent_ref: selected intent
# context_ref: selected context
# snippet_ref: selected snippet
# intent_text/context_text: set(all the code snippet extracted from html text) since currently
# we don't have any prior to differ intent and context, intent_text and context_text are the same

# due to tag completion (done by browser), the selected text recovered by saved offset might mis-match
# with the reference text, here we print such cases for manual examination.
final_annotations = []
error_count = 0
for a in parsed_confident_annotations:
    aa = {
        'post_id': a['post_id'],
        'intent_ref': '\n'.join(unescape(text) for _, text, _ in a['intent']),
        'context_ref': '\n'.join(unescape(text) if text.strip() == text_ref.strip() else unescape(text_ref) for _, text, text_ref in a['context']),
        'snippet_ref': '\n'.join(unescape(text) if text.strip() == text_ref.strip() else unescape(text_ref) for _, text, text_ref in a['snippet']),
        'intent_text': set(get_code_list((text for text, _, _ in a['intent']), False)),
        'context_text': set(get_code_list(text for text, _, _ in a['context'])),
        'snippet_text': set(get_code_list(text for text, _, _ in a['snippet'])),
    }
    for _, text, text_ref in a['snippet']:
        if text.strip() != text_ref.strip():
            print text
            print '-------------------------'
            print text_ref
            print '========================='
    for _, text, text_ref in a['context']:
        if text.strip() != text_ref.strip():
            print text
            print '-------------------------'
            print text_ref
            print '========================='
    if not aa['snippet_ref']:
        error_count += 1
    else:
        final_annotations.append(aa)

assert error_count == 0


#normalize the code selection from annotation records
#note some of selection could not be normalized, this is because the original code have syntax error
#so we just skip these posts for now
passed_count = 0
failed_count = 0
falied_list = []
for i, a in enumerate(final_annotations):
    #for code in a['context_text'] | a['snippet_text']:
    context = normalize_code(a['context_ref'])
    snippet = normalize_code(a['snippet_ref'])
    code = None
    if context is not None and snippet is not None:
        code = normalize_code(context + '\n' + snippet)
    if code is not None:
        passed_count += 1
    else:
        print a['post_id']
        falied_list.append(a)
        failed_count += 1
print failed_count, passed_count


filter_out_questions = {a['post_id']for a in falied_list}
print filter_out_questions

final_annotations = [a for a in final_annotations if a['post_id'] not in filter_out_questions]

for a in final_annotations:
    a['context_ref'] = normalize_code(a['context_ref'])
    a['snippet_ref'] = normalize_code(a['snippet_ref'])
    a['intent_ref'] = a['intent_ref'].strip()

pickle.dump(final_annotations, open('annotations.p', 'wb'))


annotated_question_ids = {annotation['post_id'] for annotation in final_annotations}
# a question denotes an SO page (title + list(answer posts))
questions = {}
for qid in annotated_question_ids:
    top_answer_ids = zip(*(sorted(question_answer_scores[qid], key=lambda x: -x[0])[:3]))[-1]
    title = titles[qid]
    snippets = set(get_code_list(posts[aid] for aid in top_answer_ids))
    normalized_snippets = set()
    for s in snippets:
        ss = normalize_code(s)
        if ss:
            normalized_snippets.add(ss)
        else:
            normalized_snippets.add(s)

    entry = {
        'title': title,
        'snippets': normalized_snippets
    }

    questions[qid] = entry
pickle.dump(questions, open('questions.p', 'wb'))


#UW's baseline: extract the only code snippet from the accepted answer
baseline = {}
for post_id in posts:
    if post_id not in accepted_posts:
        continue
    accepted_id = accepted_posts[post_id]
    code_list = list(get_code_list([posts[accepted_id]]))
    if len(code_list) == 1:
        code = code_list[0]
        code = normalize_code(code)
        if code:
            baseline[post_id] = code
pickle.dump(baseline, open('baseline.p', 'wb'))