#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic verifier for the weiqi study-pack task.

Run: python3 verify.py   (cwd = solver's final workspace root)
Prints exactly one JSON line with per_item / checks / score.
"""
import glob
import functools
import subprocess
from html.parser import HTMLParser
import html as _html
import json
import os
import re

# --------------------------------------------------------------------------
# Ground truth (author-only, frozen in task_blueprint.json objective_facts)
# Derived by running the skill's own parser (sgf_parser) on sgf_dump/ files.
# --------------------------------------------------------------------------
GAMES = [
    {
        "key": "game1",
        "page": "20240315_王宇轩_vs_李文静.html",
        "sources": [
            "sgf_dump/王宇轩VS李文静_20240315.sgf",
            "sgf_dump/wangyuxuan_vs_liwenjing_20240315.sgf",
        ],
        "date": "2024-03-15",
        "black": "王宇轩",
        "white": "李文静",
        "result": "B+R",
        "main_line_moves": 151,
        "branch_count": 4,
        "total_nodes": 168,
        "max_depth": 151,
        "start_move": 117,
    },
    {
        "key": "game2",
        "page": "20240329_赵天磊_vs_孙晓萌.html",
        "sources": ["sgf_dump/赵天磊VS孙晓萌_20240329.sgf"],
        "date": "2024-03-29",
        "black": "赵天磊",
        "white": "孙晓萌",
        "result": "W+2.5",
        "main_line_moves": 168,
        "branch_count": 3,
        "total_nodes": 186,
        "max_depth": 168,
        "start_move": 84,
    },
    {
        "key": "game3",
        "page": "20240405_陈星瑜_vs_齐昌浩.html",
        "sources": ["sgf_dump/starseven_handicap3_20240405.sgf"],
        "date": "2024-04-05",
        "black": "陈星瑜",
        "white": "齐昌浩",
        "result": "W+R",
        "main_line_moves": 96,
        "branch_count": 1,
        "total_nodes": 101,
        "max_depth": 96,
        "start_move": 0,
    },
]

WEIGHTS = {
    "pages_set": 0.20,
    "page_fidelity": 0.30,
    "deep_link": 0.20,
    "manifest": 0.20,
    "consistency": 0.10,
}


EXPECTED_GAMES = {
    '20240315_王宇轩_vs_李文静.html': json.loads('{"handicap":0,"tree":["","",[[],[],[]],"",false,[["B","pd",[[],[],[]],"",false,[["W","dd",[[],[],[]],"",false,[["B","pp",[[],[],[]],"",false,[["W","dq",[[],[],[]],"",false,[["B","do",[[],[],[]],"",false,[["W","co",[[],[],[]],"",false,[["B","cn",[[],[],[]],"",false,[["W","cp",[[],[],[]],"",false,[["B","cm",[[],[],[]],"",false,[["W","eq",[[],[],[]],"",false,[["B","fq",[[],[],[]],"",false,[["W","fp",[[],[],[]],"",false,[["B","ep",[[],[],[]],"",false,[["W","dp",[[],[],[]],"",false,[["B","qf",[[],[],[]],"",false,[["W","qc",[[],[],[]],"",false,[["B","pc",[[],[],[]],"",false,[["W","oc",[[],[],[]],"",false,[["B","nc",[[],[],[]],"",false,[["W","nd",[[],[],[]],"",false,[["B","od",[[],[],[]],"",false,[["W","nb",[[],[],[]],"",false,[["B","mb",[[],[],[]],"",false,[["W","mc",[[],[],[]],"",false,[["B","lc",[[],[],[]],"",false,[["W","kd",[[],[],[]],"",false,[["B","jd",[[],[],[]],"",false,[["W","jc",[[],[],[]],"",false,[["B","qq",[[],[],[]],"",false,[["W","pq",[[],[],[]],"",false,[["B","oq",[[],[],[]],"",false,[["W","np",[[],[],[]],"",false,[["B","nq",[[],[],[]],"",false,[["W","mq",[[],[],[]],"",false,[["B","lp",[[],[],[]],"",false,[["W","kp",[[],[],[]],"",false,[["B","ko",[[],[],[]],"",false,[["W","jp",[[],[],[]],"",false,[["B","iq",[[],[],[]],"",false,[["W","jq",[[],[],[]],"",false,[["B","kq",[[],[],[]],"",false,[["W","hr",[[],[],[]],"",false,[["B","cj",[[],[],[]],"",false,[["W","ck",[[],[],[]],"",false,[["B","dj",[[],[],[]],"",false,[["W","ej",[[],[],[]],"",false,[["B","ei",[[],[],[]],"",false,[["W","di",[[],[],[]],"",false,[["B","ci",[[],[],[]],"",false,[["W","dg",[[],[],[]],"",false,[["B","cg",[[],[],[]],"",false,[["W","ch",[[],[],[]],"",false,[["B","bh",[[],[],[]],"",false,[["W","bg",[[],[],[]],"",false,[["B","bf",[[],[],[]],"",false,[["W","cf",[[],[],[]],"",false,[["B","fd",[[],[],[]],"",false,[["W","fc",[[],[],[]],"",false,[["B","gc",[[],[],[]],"",false,[["W","hc",[[],[],[]],"",false,[["B","ic",[[],[],[]],"",false,[["W","gd",[[],[],[]],"",false,[["B","hd",[[],[],[]],"",false,[["W","ge",[[],[],[]],"",false,[["B","he",[[],[],[]],"",false,[["W","gf",[[],[],[]],"",false,[["B","hf",[[],[],[]],"",false,[["W","gg",[[],[],[]],"",false,[["B","hg",[[],[],[]],"",false,[["W","fg",[[],[],[]],"",false,[["B","dr",[[],[],[]],"",false,[["W","cr",[[],[],[]],"",false,[["B","cq",[[],[],[]],"",false,[["W","bq",[[],[],[]],"",false,[["B","bp",[[],[],[]],"",false,[["W","bo",[[],[],[]],"",false,[["B","bn",[[],[],[]],"",false,[["W","bm",[[],[],[]],"",false,[["B","bl",[[],[],[]],"",false,[["W","br",[[],[],[]],"",false,[["B","cs",[[],[],[]],"",false,[["W","bs",[[],[],[]],"",false,[["B","ds",[[],[],[]],"",false,[["W","es",[[],[],[]],"",false,[["B","qn",[[],[],[]],"",false,[["W","qm",[[],[],[]],"",false,[["B","ql",[[],[],[]],"",false,[["W","pk",[[],[],[]],"",false,[["B","pj",[[],[],[]],"",false,[["W","pl",[[],[],[]],"",false,[["B","ok",[[],[],[]],"",false,[["W","oj",[[],[],[]],"",false,[["B","oi",[[],[],[]],"",false,[["W","pi",[[],[],[]],"",false,[["B","ph",[[],[],[]],"",false,[["W","pg",[[],[],[]],"",false,[["B","pf",[[],[],[]],"",false,[["W","pe",[[],[],[]],"",false,[["B","rq",[[],[],[]],"",false,[["W","rp",[[],[],[]],"",false,[["B","ro",[[],[],[]],"",false,[["W","rn",[[],[],[]],"",false,[["B","rm",[[],[],[]],"",false,[["W","rj",[[],[],[]],"",false,[["B","rk",[[],[],[]],"",false,[["W","rl",[[],[],[]],"",false,[["B","rh",[[],[],[]],"",false,[["W","qg",[[],[],[]],"",false,[["B","qh",[[],[],[]],"",false,[["W","qi",[[],[],[]],"",false,[["B","qj",[[],[],[]],"",false,[["W","rf",[[],[],[]],"",false,[["B","fo",[[],[],[]],"",false,[["W","fn",[[],[],[]],"",false,[["B","fm",[[],[],[]],"",false,[["W","fl",[[],[],[]],"",false,[["B","fk",[[],[],[]],"",true,[["W","fj",[[],[],[]],"",false,[["B","fi",[[],[],[]],"",false,[["W","fh",[[],[],[]],"",false,[["B","en",[[],[],[]],"",false,[["W","em",[[],[],[]],"",false,[["B","el",[[],[],[]],"",false,[["W","ek",[[],[],[]],"",false,[["B","dn",[[],[],[]],"",false,[["W","dm",[[],[],[]],"",false,[["B","go",[[],[],[]],"",false,[["W","gn",[[],[],[]],"",false,[["B","gm",[[],[],[]],"",false,[["W","gl",[[],[],[]],"",false,[["B","gk",[[],[],[]],"",false,[["W","gj",[[],[],[]],"",false,[["B","gi",[[],[],[]],"",false,[["W","gh",[[],[],[]],"",false,[["B","gr",[[],[],[]],"",false,[["W","gq",[[],[],[]],"",false,[["B","gp",[[],[],[]],"",false,[["W","fr",[[],[],[]],"",false,[["B","fs",[[],[],[]],"",false,[["W","gs",[[],[],[]],"",false,[["B","ln",[[],[],[]],"",false,[["W","lm",[[],[],[]],"",false,[["B","kn",[[],[],[]],"",false,[["W","km",[[],[],[]],"",false,[["B","jn",[[],[],[]],"",false,[["W","jm",[[],[],[]],"",false,[["B","in",[[],[],[]],"",false,[["W","im",[[],[],[]],"",false,[["B","hn",[[],[],[]],"",false,[["W","hm",[[],[],[]],"",false,[["B","ll",[[],[],[]],"",false,[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]],["B","kl",[[],[],[]],"",false,[["W","jl",[[],[],[]],"",false,[["B","il",[[],[],[]],"",false,[["W","no",[[],[],[]],"",false,[["B","nn",[[],[],[]],"",false,[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]],["W","ml",[[],[],[]],"",false,[["B","mk",[[],[],[]],"",false,[["W","mj",[[],[],[]],"",false,[["B","mi",[[],[],[]],"",false,[]]]]]]]],["W","mn",[[],[],[]],"",false,[["B","mm",[[],[],[]],"",false,[["W","nm",[[],[],[]],"",false,[["B","nl",[[],[],[]],"",false,[["W","nk",[[],[],[]],"",false,[]]]]]],["W","nj",[[],[],[]],"",false,[["B","ni",[[],[],[]],"",false,[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]}'),
    '20240329_赵天磊_vs_孙晓萌.html': json.loads('{"handicap":0,"tree":["","",[[],[],[]],"",false,[["B","pd",[[],[],[]],"",false,[["W","dd",[[],[],[]],"",false,[["B","pp",[[],[],[]],"",false,[["W","dq",[[],[],[]],"",false,[["B","do",[[],[],[]],"",false,[["W","co",[[],[],[]],"",false,[["B","cn",[[],[],[]],"",false,[["W","cp",[[],[],[]],"",false,[["B","cm",[[],[],[]],"",false,[["W","eq",[[],[],[]],"",false,[["B","fq",[[],[],[]],"",false,[["W","fp",[[],[],[]],"",false,[["B","ep",[[],[],[]],"",false,[["W","dp",[[],[],[]],"",false,[["B","qf",[[],[],[]],"",false,[["W","qc",[[],[],[]],"",false,[["B","pc",[[],[],[]],"",false,[["W","oc",[[],[],[]],"",false,[["B","nc",[[],[],[]],"",false,[["W","nd",[[],[],[]],"",false,[["B","od",[[],[],[]],"",false,[["W","nb",[[],[],[]],"",false,[["B","mb",[[],[],[]],"",false,[["W","mc",[[],[],[]],"",false,[["B","lc",[[],[],[]],"",false,[["W","kd",[[],[],[]],"",false,[["B","jd",[[],[],[]],"",false,[["W","jc",[[],[],[]],"",false,[["B","qq",[[],[],[]],"",false,[["W","pq",[[],[],[]],"",false,[["B","oq",[[],[],[]],"",false,[["W","np",[[],[],[]],"",false,[["B","nq",[[],[],[]],"",false,[["W","mq",[[],[],[]],"",false,[["B","lp",[[],[],[]],"",false,[["W","kp",[[],[],[]],"",false,[["B","ko",[[],[],[]],"",false,[["W","jp",[[],[],[]],"",false,[["B","iq",[[],[],[]],"",false,[["W","jq",[[],[],[]],"",false,[["B","kq",[[],[],[]],"",false,[["W","hr",[[],[],[]],"",false,[["B","cj",[[],[],[]],"",false,[["W","ck",[[],[],[]],"",false,[["B","dj",[[],[],[]],"",false,[["W","ej",[[],[],[]],"",false,[["B","ei",[[],[],[]],"",false,[["W","di",[[],[],[]],"",false,[["B","ci",[[],[],[]],"",false,[["W","dg",[[],[],[]],"",false,[["B","cg",[[],[],[]],"",false,[["W","ch",[[],[],[]],"",false,[["B","bh",[[],[],[]],"",false,[["W","bg",[[],[],[]],"",false,[["B","bf",[[],[],[]],"",false,[["W","cf",[[],[],[]],"",false,[["B","fd",[[],[],[]],"",false,[["W","fc",[[],[],[]],"",false,[["B","gc",[[],[],[]],"",false,[["W","hc",[[],[],[]],"",false,[["B","ic",[[],[],[]],"",false,[["W","gd",[[],[],[]],"",false,[["B","hd",[[],[],[]],"",false,[["W","ge",[[],[],[]],"",false,[["B","he",[[],[],[]],"",false,[["W","gf",[[],[],[]],"",false,[["B","hf",[[],[],[]],"",false,[["W","gg",[[],[],[]],"",false,[["B","hg",[[],[],[]],"",false,[["W","fg",[[],[],[]],"",false,[["B","dr",[[],[],[]],"",false,[["W","cr",[[],[],[]],"",false,[["B","cq",[[],[],[]],"",false,[["W","bq",[[],[],[]],"",false,[["B","bp",[[],[],[]],"",false,[["W","bo",[[],[],[]],"",false,[["B","bn",[[],[],[]],"",false,[["W","bm",[[],[],[]],"",false,[["B","bl",[[],[],[]],"",false,[["W","br",[[],[],[]],"",false,[["B","cs",[[],[],[]],"",false,[["W","bs",[[],[],[]],"",false,[["B","ds",[[],[],[]],"",false,[["W","es",[[],[],[]],"",true,[["B","qn",[[],[],[]],"",false,[["W","qm",[[],[],[]],"",false,[["B","ql",[[],[],[]],"",false,[["W","pk",[[],[],[]],"",false,[["B","pj",[[],[],[]],"",false,[["W","pl",[[],[],[]],"",false,[["B","ok",[[],[],[]],"",false,[["W","oj",[[],[],[]],"",false,[["B","oi",[[],[],[]],"",false,[["W","pi",[[],[],[]],"",false,[["B","ph",[[],[],[]],"",false,[["W","pg",[[],[],[]],"",false,[["B","pf",[[],[],[]],"",false,[["W","pe",[[],[],[]],"",false,[["B","rq",[[],[],[]],"",false,[["W","rp",[[],[],[]],"",false,[["B","ro",[[],[],[]],"",false,[["W","rn",[[],[],[]],"",false,[["B","rm",[[],[],[]],"",false,[["W","rj",[[],[],[]],"",false,[["B","rk",[[],[],[]],"",false,[["W","rl",[[],[],[]],"",false,[["B","rh",[[],[],[]],"",false,[["W","qg",[[],[],[]],"",false,[["B","qh",[[],[],[]],"",false,[["W","qi",[[],[],[]],"",false,[["B","qj",[[],[],[]],"",false,[["W","rf",[[],[],[]],"",false,[["B","fo",[[],[],[]],"",false,[["W","fn",[[],[],[]],"",false,[["B","fm",[[],[],[]],"",false,[["W","fl",[[],[],[]],"",false,[["B","fk",[[],[],[]],"",false,[["W","fj",[[],[],[]],"",false,[["B","fi",[[],[],[]],"",false,[["W","fh",[[],[],[]],"",false,[["B","en",[[],[],[]],"",false,[["W","em",[[],[],[]],"",false,[["B","el",[[],[],[]],"",false,[["W","ek",[[],[],[]],"",false,[["B","dn",[[],[],[]],"",false,[["W","dm",[[],[],[]],"",false,[["B","go",[[],[],[]],"",false,[["W","gn",[[],[],[]],"",false,[["B","gm",[[],[],[]],"",false,[["W","gl",[[],[],[]],"",false,[["B","gk",[[],[],[]],"",false,[["W","gj",[[],[],[]],"",false,[["B","gi",[[],[],[]],"",false,[["W","gh",[[],[],[]],"",false,[["B","gr",[[],[],[]],"",false,[["W","gq",[[],[],[]],"",false,[["B","gp",[[],[],[]],"",false,[["W","fr",[[],[],[]],"",false,[["B","fs",[[],[],[]],"",false,[["W","gs",[[],[],[]],"",false,[["B","ln",[[],[],[]],"",false,[["W","lm",[[],[],[]],"",false,[["B","kn",[[],[],[]],"",false,[["W","km",[[],[],[]],"",false,[["B","jn",[[],[],[]],"",false,[["W","jm",[[],[],[]],"",false,[["B","in",[[],[],[]],"",false,[["W","im",[[],[],[]],"",false,[["B","hn",[[],[],[]],"",false,[["W","hm",[[],[],[]],"",false,[["B","ll",[[],[],[]],"",false,[["W","kl",[[],[],[]],"",false,[["B","jl",[[],[],[]],"",false,[["W","il",[[],[],[]],"",false,[["B","no",[[],[],[]],"",false,[["W","nn",[[],[],[]],"",false,[["B","nm",[[],[],[]],"",false,[["W","nl",[[],[],[]],"",false,[["B","nk",[[],[],[]],"",false,[["W","nj",[[],[],[]],"",false,[["B","ni",[[],[],[]],"",false,[["W","mn",[[],[],[]],"",false,[["B","mm",[[],[],[]],"",false,[["W","ml",[[],[],[]],"",false,[["B","mk",[[],[],[]],"",false,[["W","mj",[[],[],[]],"",false,[["B","",[[],[],[]],"",false,[["W","",[[],[],[]],"",false,[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]],["B","mi",[[],[],[]],"",false,[["W","mh",[[],[],[]],"",false,[["B","qp",[[],[],[]],"",false,[["W","pn",[[],[],[]],"",false,[["B","pm",[[],[],[]],"",false,[["W","on",[[],[],[]],"",false,[["B","om",[[],[],[]],"",false,[["W","ol",[[],[],[]],"",false,[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]],["W","er",[[],[],[]],"",false,[["B","qr",[[],[],[]],"",false,[["W","pr",[[],[],[]],"",false,[["B","or",[[],[],[]],"",false,[]]]]]],["B","nr",[[],[],[]],"",false,[["W","re",[[],[],[]],"",false,[["B","rd",[[],[],[]],"",false,[["W","rc",[[],[],[]],"",false,[["B","rb",[[],[],[]],"",false,[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]}'),
    '20240405_陈星瑜_vs_齐昌浩.html': json.loads('{"handicap":3,"tree":["","",[["dp","pd","pp"],[],[]],"",false,[["B","pd",[[],[],[]],"",false,[["W","dd",[[],[],[]],"",false,[["B","pp",[[],[],[]],"",false,[["W","dq",[[],[],[]],"",false,[["B","do",[[],[],[]],"",false,[["W","co",[[],[],[]],"",false,[["B","cn",[[],[],[]],"",false,[["W","cp",[[],[],[]],"",false,[["B","cm",[[],[],[]],"",false,[["W","eq",[[],[],[]],"",false,[["B","fq",[[],[],[]],"",false,[["W","fp",[[],[],[]],"",false,[["B","ep",[[],[],[]],"",false,[["W","dp",[[],[],[]],"",false,[["B","qf",[[],[],[]],"",false,[["W","qc",[[],[],[]],"",false,[["B","pc",[[],[],[]],"",false,[["W","oc",[[],[],[]],"",false,[["B","nc",[[],[],[]],"",false,[["W","nd",[[],[],[]],"",false,[["B","od",[[],[],[]],"",false,[["W","nb",[[],[],[]],"",false,[["B","mb",[[],[],[]],"",false,[["W","mc",[[],[],[]],"",false,[["B","lc",[[],[],[]],"",false,[["W","kd",[[],[],[]],"",false,[["B","jd",[[],[],[]],"",false,[["W","jc",[[],[],[]],"",false,[["B","qq",[[],[],[]],"",false,[["W","pq",[[],[],[]],"",false,[["B","oq",[[],[],[]],"",false,[["W","np",[[],[],[]],"",false,[["B","nq",[[],[],[]],"",false,[["W","mq",[[],[],[]],"",false,[["B","lp",[[],[],[]],"",false,[["W","kp",[[],[],[]],"",false,[["B","ko",[[],[],[]],"",false,[["W","jp",[[],[],[]],"",false,[["B","iq",[[],[],[]],"",false,[["W","jq",[[],[],[]],"",false,[["B","kq",[[],[],[]],"",false,[["W","hr",[[],[],[]],"",false,[["B","cj",[[],[],[]],"",false,[["W","ck",[[],[],[]],"",false,[["B","dj",[[],[],[]],"",false,[["W","ej",[[],[],[]],"",false,[["B","ei",[[],[],[]],"",false,[["W","di",[[],[],[]],"",false,[["B","ci",[[],[],[]],"",false,[["W","dg",[[],[],[]],"",false,[["B","cg",[[],[],[]],"",false,[["W","ch",[[],[],[]],"",false,[["B","bh",[[],[],[]],"",false,[["W","bg",[[],[],[]],"",false,[["B","bf",[[],[],[]],"",false,[["W","cf",[[],[],[]],"",false,[["B","fd",[[],[],[]],"",false,[["W","fc",[[],[],[]],"",false,[["B","gc",[[],[],[]],"",false,[["W","hc",[[],[],[]],"",false,[["B","ic",[[],[],[]],"",false,[["W","gd",[[],[],[]],"",false,[["B","hd",[[],[],[]],"",false,[["W","ge",[[],[],[]],"",false,[["B","he",[[],[],[]],"",false,[["W","gf",[[],[],[]],"",false,[["B","hf",[[],[],[]],"",false,[["W","gg",[[],[],[]],"",false,[["B","hg",[[],[],[]],"",false,[["W","fg",[[],[],[]],"",false,[["B","dr",[[],[],[]],"",false,[["W","cr",[[],[],[]],"",false,[["B","cq",[[],[],[]],"",false,[["W","bq",[[],[],[]],"",false,[["B","bp",[[],[],[]],"",false,[["W","bo",[[],[],[]],"",false,[["B","bn",[[],[],[]],"",false,[["W","bm",[[],[],[]],"",false,[["B","bl",[[],[],[]],"",false,[["W","br",[[],[],[]],"",false,[["B","cs",[[],[],[]],"",false,[["W","bs",[[],[],[]],"",false,[["B","ds",[[],[],[]],"",false,[["W","es",[[],[],[]],"",false,[["B","qn",[[],[],[]],"",false,[["W","qm",[[],[],[]],"",false,[["B","ql",[[],[],[]],"",false,[["W","pk",[[],[],[]],"",false,[["B","pj",[[],[],[]],"",false,[["W","pl",[[],[],[]],"",false,[["B","ok",[[],[],[]],"",false,[["W","oj",[[],[],[]],"",false,[["B","oi",[[],[],[]],"",false,[["W","pi",[[],[],[]],"",false,[["B","ph",[[],[],[]],"",false,[["W","pg",[[],[],[]],"",false,[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]],["W","pf",[[],[],[]],"",false,[["B","pe",[[],[],[]],"",false,[["W","rq",[[],[],[]],"",false,[["B","rp",[[],[],[]],"",false,[]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]}'),
}

RUNTIME_PROBE = r"""const vm = require('vm');
const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
const sandbox = vm.createContext({}, {codeGeneration: {strings: false, wasm: false}});
function execute(code) {return vm.runInContext(code, sandbox, {timeout: 1500});}
const bootstrap = String.raw`let draws = 0;
const timers = [];
const elements = new Map();
function assert(ok, message) { if (!ok) throw Error(message); }
const context2d = {};
for (const key of ['fillRect','clearRect','beginPath','moveTo','lineTo','stroke','arc','fill','fillText','strokeText','save','restore','closePath','rect','setTransform']) {
    context2d[key] = () => { draws++; };
}
context2d.createRadialGradient = () => ({addColorStop() {}});
function element(tag, attrs = {}) {
    const classes = new Set((attrs.class || '').split(/\s+/));
    return {
        tagName: tag.toUpperCase(), attrs, children: [], style: {}, disabled: 'disabled' in attrs,
        clientWidth: 720, width: 720, height: 720, textContent: '', value: '',
        classList: {add: x => classes.add(x), remove: x => classes.delete(x), contains: x => classes.has(x), toggle(x) {classes.has(x) ? classes.delete(x) : classes.add(x);}},
        appendChild(x) {this.children.push(x);}, addEventListener() {},
        getContext() {assert(tag === 'canvas', 'board is not canvas'); return context2d;},
        getBoundingClientRect() {return {left: 0, top: 0};},
        set innerHTML(s) {
            this.children = [];
            this.value = s.replace(/&(?:#[xX][0-9a-fA-F]+|#[0-9]+|[A-Za-z][A-Za-z0-9]*);?/g, token => input.entities[token] ?? token);
        }
    };
}
const nodes = input.elements.map(e => element(e.tag, e.attrs));
for (let i = 0; i < input.elements.length; i++) {
    const e = input.elements[i];
    nodes[i].parentElement = e.parent === null ? null : nodes[e.parent];
    if (e.attrs.id) {assert(!elements.has(e.attrs.id), 'duplicate element id'); elements.set(e.attrs.id, nodes[i]);}
}
const container = input.elements.find(e => (e.attrs.class || '').split(/\s+/).includes('board-container'));
assert(container, 'board container missing');
const document = {
    getElementById: id => elements.get(id) || null,
    querySelector: selector => selector === '.board-container' ? element(container.tag, container.attrs) : null,
    createElement: tag => element(tag), addEventListener() {}
};
class AudioContext {
    constructor() {this.state = 'running'; this.sampleRate = 44100; this.currentTime = 0;}
    resume() {return Promise.resolve();}
    createBuffer(channels, size) {return {getChannelData: () => new Float32Array(size)};}
    createBufferSource() {return {connect() {}, start() {}, stop() {}};}
    createBiquadFilter() {return {frequency: {}, Q: {}, connect() {}};}
    createGain() {return {gain: {setValueAtTime() {}, exponentialRampToValueAtTime() {}}, connect() {}};}
}
const window = {innerWidth: 1024, innerHeight: 1000, AudioContext, addEventListener() {}};
const console = {log() {}, warn() {}};
function setTimeout(f) {timers.push(f); return timers.length;}
function setInterval(f) {timers.push(f); return timers.length;}
function clearTimeout() {}
function clearInterval() {}
`;
execute("const input = " + JSON.stringify(input) + ";\n" + bootstrap);
for (const script of input.scripts) execute(script);
const checks = String.raw`for (let i = 0; i < timers.length && i < 20; i++) {timers[i]();}
assert(timers.length < 20, 'excessive initialization timers');
const initial = (getMovesToCurrent().length);
assert(initial === input.start_move, 'initial move mismatch');
assert(draws > 30, 'board did not draw');
assert(elements.get('board')?.tagName === 'CANVAS', 'canvas missing');
const treeSnapshot = JSON.stringify(tree);
function click(id) {
    const e = elements.get(id);
    assert(e && !e.disabled && e.attrs.onclick, id + ' is not an active button');
    assert(e.tagName === 'BUTTON', id + ' is not a button');
    const handler = id === 'nextBtn' ? nextMove : prevMove;
    const name = id === 'nextBtn' ? 'nextMove' : 'prevMove';
    assert(e.attrs.onclick.replace(/\s/g, '').replace(/;$/, '') === name + '()', id + ' handler mismatch');
    handler();
}
const beforeDraw = draws;
click('nextBtn');
assert((getMovesToCurrent().length) === initial + 1, 'next button failed');
assert(draws > beforeDraw, 'next move did not redraw');
click('prevBtn');
assert((getMovesToCurrent().length) === initial, 'previous button failed');
(goToMove(0));
assert((getMovesToCurrent().length) === 0, 'go-to-start failed');
goToMove(input.main_line_moves);
assert((getMovesToCurrent().length) === input.main_line_moves, 'go-to-end failed');
(goToMove(0));
let branchFound = false;
for (let i = 0; i < input.main_line_moves; i++) {
    if ((getCurrentChildren().length) > 1) {
        const list = elements.get('variationList');
        assert(list && list.children.length > 0, 'variation controls missing');
        const before = (JSON.stringify(getCurrentChildren()[1]));
        const button = list.children[0];
        assert(typeof button.onclick === 'function', 'variation button inactive');
        button.onclick();
        assert((JSON.stringify(getCurrentNode())) === before, 'variation selection failed');
        branchFound = true;
        break;
    }
    click('nextBtn');
}
assert(branchFound, 'no playable variation');
({ok: true, initial, tree: JSON.parse(treeSnapshot), board_size: BOARD_SIZE, handicap_stones: JSON.parse(JSON.stringify(handicapStones))});
`;
process.stdout.write(JSON.stringify(execute(checks)));
"""


def _values(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _point(value, allow_pass=False):
    text = '' if value is None else str(value)
    if allow_pass and text in ('', 'tt', 'TT'):
        return ''
    if not re.fullmatch('[a-s]{2}', text):
        raise ValueError('invalid board coordinate')
    return text


def _points(value):
    points = set()
    for item in _values(value):
        pair = str(item).split(':')
        if len(pair) == 1:
            points.add(_point(pair[0]))
        elif len(pair) == 2:
            a, b = map(_point, pair)
            if a[0] > b[0] or a[1] > b[1]:
                raise ValueError('invalid setup range')
            points.update(chr(x) + chr(y) for x in range(ord(a[0]), ord(b[0]) + 1)
                          for y in range(ord(a[1]), ord(b[1]) + 1))
        else:
            raise ValueError('invalid setup coordinates')
    return sorted(points)


def _scalar(value, default=''):
    values = _values(value)
    if not values:
        return default
    if len(values) != 1:
        raise ValueError('expected one property value')
    return str(values[0])


def _tree_semantics(tree):
    props = tree.get('properties', {})
    color = tree.get('color')
    if color not in (None, 'B', 'W'):
        raise ValueError('invalid move color')
    coord = _point(tree.get('coord'), allow_pass=True) if color else ''
    if 'B' in props and 'W' in props:
        raise ValueError('two colors in one move')
    for move_color in ('B', 'W'):
        if move_color in props and (move_color != color or _point(_scalar(props[move_color]), True) != coord):
            raise ValueError('move properties disagree with played move')
    setup = [_points(props.get(key)) for key in ('AB', 'AW', 'AE')]
    player = _scalar(props.get('PL'))
    if player not in ('', 'B', 'W'):
        raise ValueError('invalid player-to-move')
    key_move = bool(color) and ('1' in [str(v) for v in _values(props.get('TE'))]
                               or any('【关键手】' in str(v) for v in _values(props.get('C'))))
    children = [_tree_semantics(child) for child in tree.get('children', [])]
    if children:
        children = children[:1] + sorted(children[1:], key=lambda x: json.dumps(x, ensure_ascii=False))
    return [color or '', coord, setup, player, key_move, children]


def _tree_matches(tree, game):
    try:
        props = tree.get('properties', {})
        for key, expected in [('PB', game['black']), ('PW', game['white']), ('DT', game['date']),
                              ('RE', game['result']), ('SZ', '19')]:
            if _scalar(props.get(key)) != expected:
                return False
        if int(_scalar(props.get('HA'), '0')) != EXPECTED_GAMES[game['page']]['handicap']:
            return False
        return _tree_semantics(tree) == EXPECTED_GAMES[game['page']]['tree']
    except (TypeError, ValueError, AttributeError, RecursionError):
        return False


def _board_setup_matches(result, game):
    try:
        actual = result['handicap_stones']
        if result['board_size'] != 19 or not isinstance(actual, list):
            return False
        points = []
        for stone in actual:
            x, y = stone['x'], stone['y']
            if type(x) is not int or type(y) is not int or not (0 <= x < 19 and 0 <= y < 19):
                return False
            points.append(chr(97 + x) + chr(97 + y))
        return sorted(points) == EXPECTED_GAMES[game['page']]['tree'][2][0]
    except (KeyError, TypeError, ValueError):
        return False


class _PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []
        self.scripts = []
        self.script = None
        self.stack = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        parent = self.stack[-1] if self.stack else None
        self.elements.append({'tag': tag, 'attrs': attrs, 'parent': parent})
        if tag not in ('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'):
            self.stack.append(len(self.elements) - 1)
        if tag == 'script':
            kind = (attrs.get('type') or '').strip().lower()
            self.script = [] if kind in ('', 'text/javascript', 'application/javascript') and 'src' not in attrs else None

    def handle_data(self, data):
        if self.script is not None:
            self.script.append(data)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.elements[self.stack[i]]['tag'] == tag:
                del self.stack[i:]
                break
        if tag == 'script':
            if self.script is not None:
                self.scripts.append(''.join(self.script))
            self.script = None


def _obviously_hidden(parser, raw):
    board = next((i for i, e in enumerate(parser.elements) if e['attrs'].get('id') == 'board'), None)
    if board is None:
        return True
    ancestors = []
    while board is not None:
        ancestors.append(parser.elements[board])
        board = parser.elements[board]['parent']
    hidden = re.compile(r'(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*(?:hidden|collapse)|opacity\s*:\s*0(?:\.0*)?)\s*(?:!important\s*)?(?:;|$)', re.I)
    for e in ancestors:
        if 'hidden' in e['attrs'] or hidden.search(e['attrs'].get('style') or ''):
            return True
    styles = '\n'.join(re.findall(r'<style\b[^>]*>(.*?)</style\s*>', raw, re.I | re.S))
    styles = re.sub(r'/\*.*?\*/', '', styles, flags=re.S)
    for selectors, declarations in re.findall(r'([^{}]+)\{([^{}]*)\}', styles):
        if not hidden.search(declarations):
            continue
        for selector in selectors.split(','):
            selector = selector.strip()
            for e in ancestors:
                names = {e['tag'], '*'}
                if e['attrs'].get('id'):
                    names.add('#' + e['attrs']['id'])
                names.update('.' + c for c in e['attrs'].get('class', '').split())
                if selector in names:
                    return True
    return False


@functools.lru_cache(maxsize=3)
def _page_runtime(page):
    game = next(g for g in GAMES if g['page'] == page)
    try:
        parser = _PageParser()
        with open(os.path.join('study_pack', page), encoding='utf-8') as f:
            raw = f.read()
        parser.feed(raw)
        if _obviously_hidden(parser, raw):
            return False, 'board or page is hidden', None
        entities = {m.group(): _html.unescape(m.group()) for script in parser.scripts
                    for m in re.finditer(r'&(?:#[xX][0-9a-fA-F]+|#[0-9]+|[A-Za-z][A-Za-z0-9]*);?', script)}
        payload = {'elements': parser.elements, 'scripts': parser.scripts, 'entities': entities,
                   'start_move': game['start_move'], 'main_line_moves': game['main_line_moves']}
        proc = subprocess.run(['node', '--permission', '--max-old-space-size=128', '-e', RUNTIME_PROBE],
                              input=json.dumps(payload), capture_output=True, text=True,
                              cwd='/tmp', timeout=15, env={'PATH': os.environ.get('PATH', '/usr/local/bin:/usr/bin:/bin')})
        if proc.returncode:
            return False, 'page script or navigation failed', None
        result = json.loads(proc.stdout)
        if not result.get('ok') or not _tree_matches(result.get('tree'), game) or not _board_setup_matches(result, game):
            return False, 'page tree differs from source game', None
        return True, 'page initialization and navigation passed', result['initial']
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        return False, str(e)[:160], None


def _extract_embedded_tree(raw_text):
    """Pull the tree JSON embedded by the official replay tool
    (template decodes it via textarea.innerHTML)."""
    m = re.search(r"textarea\.innerHTML = '(.*?)';", raw_text, re.S)
    if not m:
        return None
    try:
        return json.loads(_html.unescape(m.group(1)))
    except Exception:
        return None


def _tree_max_depth(node):
    depth = node.get("move_number", 0)
    for ch in node.get("children", []):
        depth = max(depth, _tree_max_depth(ch))
    return depth


def _tree_total(node):
    n = 1
    for ch in node.get("children", []):
        n += _tree_total(ch)
    return n


def _tree_branch_count(node):
    children = node.get("children", [])
    b = (len(children) - 1) if len(children) > 1 else 0
    for ch in children:
        b += _tree_branch_count(ch)
    return b


def _tree_mainline(node):
    d = 0
    n = node
    while n.get("children"):
        n = n["children"][0]
        d += 1
    return d


def _default_move(raw_text):
    m = re.search(r"const DEFAULT_MOVE = (-?\d+)\s*;", raw_text)
    return int(m.group(1)) if m else None


def check_pages_set():
    """R1: study_pack/ contains exactly the 3 correctly named pages."""
    pages_dir = "study_pack"
    expected = {g["page"] for g in GAMES}
    actual = set()
    try:
        for p in glob.glob(os.path.join(pages_dir, "*.html")):
            actual.add(os.path.basename(p))
    except Exception:
        pass
    found = len(expected & actual)
    recall = found / len(expected)
    extras = actual - expected
    no_extra = 1.0 if not extras else 0.0
    score = 0.6 * recall + 0.4 * no_extra
    detail = "found {}/{} expected pages; extras={}".format(
        found, len(expected), sorted(extras) if extras else "none")
    return score, detail


def check_page_fidelity():
    """R2: each page carries the correct game content as produced by the
    official tool: players (no mojibake), result text, 19x19 board, embedded
    tree statistics matching the source SGF."""
    per_game = []
    details = []
    for g in GAMES:
        path = os.path.join("study_pack", g["page"])
        subs = []
        try:
            raw = open(path, "r", encoding="utf-8").read()
        except Exception:
            details.append("{}: missing/unreadable".format(g["page"]))
            per_game.append(0.0)
            continue
        subs.append(1.0 if g["black"] in raw else 0.0)            # black name intact
        subs.append(1.0 if g["white"] in raw else 0.0)            # white name intact
        subs.append(1.0 if "\ufffd" not in raw else 0.0)          # no mojibake chars
        subs.append(1.0 if g["result"] in raw else 0.0)           # result shown
        subs.append(1.0 if re.search(r"const BOARD_SIZE = 19\s*;", raw) else 0.0)
        tree = _extract_embedded_tree(raw)
        if tree is None:
            subs += [0.0, 0.0]
            details.append("{}: no decodable embedded tree".format(g["page"]))
        else:
            subs.append(1.0 if _tree_total(tree) == g["total_nodes"] else 0.0)
            subs.append(1.0 if _tree_branch_count(tree) == g["branch_count"]
                        and _tree_max_depth(tree) == g["max_depth"] else 0.0)
            details.append("{}: embedded tree ok".format(g["page"]))
        runtime_ok, runtime_detail, _ = _page_runtime(g['page'])
        valid_tree = _tree_matches(tree, g)
        per_game.append(sum(subs) / len(subs) if runtime_ok and valid_tree else 0.0)
        details.append(runtime_detail)
    score = sum(per_game) / len(per_game)
    return score, "; ".join(details)


def check_deep_link():
    """R3: DEFAULT_MOVE matches the policy-derived key move per page."""
    hits = 0
    details = []
    for g in GAMES:
        path = os.path.join("study_pack", g["page"])
        try:
            raw = open(path, "r", encoding="utf-8").read()
            dm = _default_move(raw)
        except Exception:
            dm = None
        runtime_ok, _, initial = _page_runtime(g["page"])
        ok = (runtime_ok and dm == g["start_move"] and initial == g["start_move"])
        hits += 1 if ok else 0
        details.append("{}: DEFAULT_MOVE={} expected {}".format(g["page"], dm, g["start_move"]))
    return hits / len(GAMES), "; ".join(details)


def _load_manifest():
    try:
        with open(os.path.join("study_pack", "manifest.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None
    if isinstance(data, dict):
        games = data.get("games")
        if isinstance(games, list):
            return games
    if isinstance(data, list):  # tolerate a bare list
        return data
    return None


def _match_entry(games_list, g):
    """Find the manifest entry for ground-truth game g, by page name or by
    (date, black, white)."""
    for e in games_list:
        if not isinstance(e, dict):
            continue
        if str(e.get("page", "")).split("/")[-1] == g["page"]:
            return e
    for e in games_list:
        if not isinstance(e, dict):
            continue
        if (str(e.get("date")) == g["date"] and str(e.get("black")) == g["black"]
                and str(e.get("white")) == g["white"]):
            return e
    return None


def check_manifest():
    """R4: manifest content is complete and accurate per the spec."""
    games_list = _load_manifest()
    if games_list is None:
        return 0.0, "manifest.json missing, unparsable, or has no 'games' list"
    if len(games_list) != len(GAMES):
        count_ok = 0.0
        cnt_detail = "games count={} expected {}".format(len(games_list), len(GAMES))
    else:
        count_ok = 1.0
        cnt_detail = "games count=3 ok"

    field_names = ["source", "page", "date", "black", "white", "result",
                   "main_line_moves", "branch_count", "start_move"]
    game_scores = []
    details = []
    for g in GAMES:
        e = _match_entry(games_list, g)
        if e is None:
            game_scores.append(0.0)
            details.append("{}: no matching entry".format(g["page"]))
            continue
        fs = []
        src_ok = any(str(e.get("source", "")).replace("\\", "/").endswith(s)
                     or str(e.get("source", "")).replace("\\", "/") == s
                     for s in g["sources"])
        fs.append(1.0 if src_ok else 0.0)
        fs.append(1.0 if str(e.get("page", "")).split("/")[-1] == g["page"] else 0.0)
        fs.append(1.0 if str(e.get("date")) == g["date"] else 0.0)
        fs.append(1.0 if str(e.get("black")) == g["black"] else 0.0)
        fs.append(1.0 if str(e.get("white")) == g["white"] else 0.0)
        fs.append(1.0 if str(e.get("result")) == g["result"] else 0.0)
        fs.append(1.0 if _as_int(e.get("main_line_moves")) == g["main_line_moves"] else 0.0)
        fs.append(1.0 if _as_int(e.get("branch_count")) == g["branch_count"] else 0.0)
        fs.append(1.0 if _as_int(e.get("start_move")) == g["start_move"] else 0.0)
        game_scores.append(sum(fs) / len(fs))
        bad = [field_names[i] for i, v in enumerate(fs) if v == 0.0]
        details.append("{}: {}".format(g["page"], "ok" if not bad else "bad fields " + ",".join(bad)))
    per_game = sum(game_scores) / len(game_scores)
    score = 0.2 * count_ok + 0.8 * per_game
    return score, cnt_detail + "; " + "; ".join(details)


def _as_int(v):
    try:
        return int(v)
    except Exception:
        return None


def check_consistency():
    """R5: manifest agrees with generated pages (page exists; start_move ==
    DEFAULT_MOVE; branch_count and main_line_moves match the embedded tree)."""
    games_list = _load_manifest()
    if games_list is None:
        return 0.0, "manifest unavailable"
    per_game = []
    details = []
    for g in GAMES:
        e = _match_entry(games_list, g)
        page_ref = (str(e.get("page", "")) if isinstance(e, dict) else "")
        page_path = os.path.join("study_pack", page_ref) if page_ref else ""
        subs = []
        raw = None
        if e is not None and page_ref and os.path.isfile(page_path):
            subs.append(1.0)
            try:
                raw = open(page_path, "r", encoding="utf-8").read()
            except Exception:
                raw = None
        else:
            subs.append(0.0)
        if raw is not None:
            dm = _default_move(raw)
            subs.append(1.0 if dm is not None and _as_int(e.get("start_move")) == dm else 0.0)
            tree = _extract_embedded_tree(raw)
            if tree is not None:
                subs.append(1.0 if _as_int(e.get("branch_count")) == _tree_branch_count(tree) else 0.0)
                subs.append(1.0 if _as_int(e.get("main_line_moves")) == _tree_mainline(tree) else 0.0)
            else:
                subs += [0.0, 0.0]
        else:
            subs += [0.0, 0.0, 0.0]
        per_game.append(sum(subs) / len(subs))
        details.append("{}: {:.2f}".format(g["page"], per_game[-1]))
    return sum(per_game) / len(per_game), "; ".join(details)


def main():
    checks = [
        ("pages_set", check_pages_set),
        ("page_fidelity", check_page_fidelity),
        ("deep_link", check_deep_link),
        ("manifest", check_manifest),
        ("consistency", check_consistency),
    ]
    per_item = {}
    out_checks = []
    total_w = 0.0
    total_s = 0.0
    for cid, fn in checks:
        try:
            score, detail = fn()
            score = max(0.0, min(1.0, float(score)))
        except Exception as exc:  # individual check failure only zeroes itself
            score, detail = 0.0, "exception: {}".format(exc)
        per_item[cid] = round(score, 4)
        w = WEIGHTS[cid]
        out_checks.append({"id": cid, "weight": w, "score": round(score, 4), "detail": detail[:500]})
        total_w += w
        total_s += w * score
    overall = round(total_s / total_w, 4) if total_w else 0.0
    print(json.dumps({"per_item": per_item, "checks": out_checks, "score": overall},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
