# -*- coding: utf-8 -*-
"""
Created on Mon May 23 12:45:39 2022

@author: Unrated
"""

from .pull import pull
from config import *
from ext import get_ext

import pygit2
import watchdog
from collections import namedtuple
from contextlib import suppress
from pathlib import Path
import jinja2
import json
import markdown
import os
import pybtex.database
import re
import shlex
import shutil

def build_single(single_chapter):
    md = markdown.Markdown(extensions=EXT)

    print("Making contents folder...")
    with suppress(FileExistsError):
        (O_NAME/CONTENTS_NAME).mkdir()

    print("Copying res folder...")
    with suppress(FileNotFoundError, FileExistsError):
        shutil.copytree(AAA_CLONE_PATH/"res", O_NAME/"res")

    with suppress(FileNotFoundError, FileExistsError):
        shutil.copytree(AAA_CLONE_PATH/CONTENTS_NAME/"cc", O_NAME/CONTENTS_NAME/"cc")

    print("Done making, looking for the chapter...")
    chapter_md = next((AAA_CLONE_PATH / CONTENTS_NAME / single_chapter).glob('*.md'))
    chapter = chapter_md.parent.relative_to(AAA_CLONE_PATH/CONTENTS_NAME)

    print("Looking for the template...")

    print("Reading...")
    template = jinja2.Template(TEMPLATE_PATH.read_text())
    print("Template ready!")

    print("Building Pygments...")
    os.system(f"pygmentize -S {PYGMENT_THEME} -f html -a .codehilite > {O_NAME}/pygments.css")

    print("Parsing SUMMARY.md...")
    summary = parse_summary((AAA_PATH / SUMMARY_NAME).read_text())

    print("Opening bibtex...")
    bib_database = pybtex.database.parse_file(AAA_CLONE_PATH / "literature.bib")

    print("Opening book.json...")
    with open(CONTENTS_NAME / "book.json") as bjs:
        book_json = json.load(bjs)

    print("Creating rendering pipeline...")
    renderer = get_ext(bib_database, PYGMENT_THEME, md)

    print("Rendering chapters...")
    render_chapter(chapter, renderer, template, summary, book_json)

    # only applicable if there was no initial algorithm-archive clone
    print("Moving favicon.ico...")
    with suppress(FileNotFoundError, FileExistsError):
        shutil.copy(FAVICON_PATH, O_NAME / "favicon.ico")

    print("Moving styles...")
    with suppress(FileNotFoundError, FileExistsError):
        shutil.copytree(STYLE_PATH, O_NAME / "styles")

    print("Parsing redirects...")
    with open(AAA_PATH / "redirects.json") as rjs_file:
        rjs = json.load(rjs_file)

    rjs = {i["from"]: i["to"] for i in rjs["redirects"]}
    with open(f"{O_NAME}/redirects.json", 'w') as rjs_file:
        json.dump(rjs, rjs_file)

    print("Rendering index...")
    (O_NAME / "index.html").write_text(
            render_one((CONTENTS_NAME / INDEX_NAME).read_text(), f"{O_NAME}/", 0,
                renderer, template, summary, book_json)) 
    print("Done!")


SummaryEntry = namedtuple('SummaryEntry', ['name', 'link', 'depth'])


def parse_summary(summary):
    summary = summary.replace(".md", ".html") \
        .replace("(contents", "(/contents") \
        .replace('* ', '') \
        .replace('README', '/index')
    summary_parsed = []
    for index, line in enumerate(summary.split('\n')[2:-1]):
        indent, rest = line.split('[')
        name, link = rest.split('](')
        link = Path(link.rstrip()[:-1])
        current_indent = len(indent) // SUMMARY_INDENT_LEVEL
        summary_parsed.append(SummaryEntry(name, link, current_indent))
    return summary_parsed

def render_chapter(chapter, renderer, template, summary, book_json):
    with suppress(FileExistsError):
        (O_NAME/CONTENTS_NAME/chapter).mkdir()

    with suppress(FileNotFoundError, FileExistsError):
        # dirty hack but it works
        shutil.copyfile(AAA_CLONE_PATH/CONTENTS_NAME/"cc"/"CC-BY-SA_icon.svg",
                        O_NAME/CONTENTS_NAME/chapter/"CC-BY-SA_icon.svg")

    with suppress(FileNotFoundError, FileExistsError):
        shutil.copytree(AAA_CLONE_PATH/CONTENTS_NAME/chapter/"res",
                O_NAME/CONTENTS_NAME/chapter/"res")
    
    with suppress(FileNotFoundError, FileExistsError):
        shutil.copytree(AAA_CLONE_PATH/CONTENTS_NAME/chapter/"code",
                O_NAME/CONTENTS_NAME/chapter/"code")
    try:
        md_file: str = next((CONTENTS_NAME/CONTENTS_NAME/chapter).glob('*.md'))
    except StopIteration:
        return
    out_file = O_NAME/CONTENTS_NAME/chapter/md_file.name.replace('.md', '.html')

    try:
        index = next(index for (index, _) in filter(lambda x: out_file.name == x[1].link.name,
                                                    enumerate(summary)))
    except StopIteration:
        return
    contents: str = render_one(md_file.read_text(), f"{CONTENTS_NAME}/{CONTENTS_NAME}/{chapter}",
                               index, renderer, template, summary, book_json)
    out_file.write_text(contents, encoding='utf-8')

def render_one(text, code_dir, index, renderer, template, summary, book_json) -> str:
    finalized = renderer(text, code_dir)
    rendered = template.render(md_text=finalized, summary=summary, index=index, enumerate=enumerate,
                               bjs=json.dumps(book_json))
    return rendered