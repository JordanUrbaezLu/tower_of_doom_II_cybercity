#!/usr/bin/env node
'use strict';
// =============================================================================
// tools/lint_tod_gsc_strict.js - the BO3 GSC compiler's strict-syntax rules, checked BEFORE the linker.
//
// WHY (2026-10-03): the linker compiles every zoned script at the very END of a build and stops at the FIRST script
// error, printing only "No generated data for <file>". Build 6 of the war damage pass baked for 20 minutes and then
// died on one unwrapped ternary in a peer's never-compiled script (_tod_haven.gsc:963). No other gate compiles GSC:
// the arity lint checks calls, and the gsc_eval-based harnesses ACCEPT the shapes the real compiler refuses. This
// lint runs at the start of the gate phase, so the same mistake costs seconds.
//
// RULES (each one a real link-killer in this repo's history):
//   TERNARY      a `?` whose innermost bracket is not an expression-group paren: inside call arguments
//                (`f( ( c ) ? a : b )`), in [ ], or with no paren at all (`x = c ? a : b;`). Write `( c ? a : b )`.
//   PAREN_FIELD  `( expr ).field` - a field read off a parenthesized expression.
//   DIRECTIVE    a #using after #precache, #namespace or the first function (a #using after #insert compiles).
//   NO_FUNCTION  a top-level definition without the `function` keyword.
//   UNINIT       a local read in a function that never assigns it (params, `=`/op-assignments, element assignment,
//                foreach variables and waittill / waittillmatch outputs count as assignments; ALL_CAPS = a macro).
//   BALANCE      unbalanced ( [ {.
// CALIBRATED: zero hits on the 108 scripts that compiled in the 13:18 build; the --selftest fixtures (below) must each
// be caught, and the clean ones must stay clean. It does NOT prove a file compiles - it rules out these classes.
//
// Usage:  node tools/lint_tod_gsc_strict.js              every scripts/**/*.gsc|csc (exit 1 on any hit)
//         node tools/lint_tod_gsc_strict.js <files...>   just those
//         node tools/lint_tod_gsc_strict.js --selftest   the fixtures only
// =============================================================================
const fs = require('fs');
const path = require('path');

const KEYWORDS = new Set(('if else for foreach in while do switch case default break continue return wait waittillframeend ' +
  'thread function private autoexec self level game anim undefined true false world childthread new const').split(' '));
const STMT_PAREN = new Set(['if', 'while', 'for', 'foreach', 'switch']);
const ASSIGN_OPS = new Set(['=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=', '++', '--']);

function tokenize(src) {
  const toks = [];
  let i = 0, line = 1, lineStart = true;
  const n = src.length;
  const push = (t, v, l) => { toks.push({ t, v, line: l }); lineStart = false; };
  while (i < n) {
    const c = src[i];
    if (c === '\n') { line++; i++; lineStart = true; continue; }
    if (c === ' ' || c === '\t' || c === '\r') { i++; continue; }
    if (c === '/' && src[i + 1] === '/') { while (i < n && src[i] !== '\n') i++; continue; }
    if (c === '/' && src[i + 1] === '*') { i += 2; while (i < n && !(src[i] === '*' && src[i + 1] === '/')) { if (src[i] === '\n') line++; i++; } i += 2; continue; }
    if (c === '/' && src[i + 1] === '#') { i += 2; continue; }             // dev block open: its code is checked as code
    if (c === '#' && src[i + 1] === '/') { i += 2; continue; }             // dev block close
    if (c === '#' && !lineStart) {                                         // mid-line #animtree / #"hash" = a value
      let j = i + 1;
      if (src[j] === '"') { j++; while (j < n && src[j] !== '"') j++; j++; } else while (j < n && /\w/.test(src[j])) j++;
      push('anim', src.slice(i, j), line); i = j; continue;
    }
    if (c === '#') {                                                        // a directive: to end of line (\ continues it)
      const l0 = line; let j = i; let text = '';
      while (j < n) {
        if (src[j] === '\n') { if (src[j - 1] === '\\' || (src[j - 1] === '\r' && src[j - 2] === '\\')) { line++; text += ' '; j++; continue; } break; }
        text += src[j]; j++;
      }
      const m = text.match(/^#\s*(\w+)/);
      push('dir', m ? m[1] : '#', l0);
      i = j; continue;
    }
    if (c === '"' || (c === '&' && src[i + 1] === '"')) {
      const l0 = line; let j = i + (c === '&' ? 2 : 1);
      while (j < n && src[j] !== '"') { if (src[j] === '\\') j++; if (src[j] === '\n') line++; j++; }
      push('str', src.slice(i, j + 1), l0); i = j + 1; continue;
    }
    if (/[A-Za-z_]/.test(c)) {
      let j = i; while (j < n && /\w/.test(src[j])) j++;
      while (src[j] === ':' && src[j + 1] === ':' && /[A-Za-z_]/.test(src[j + 2] || '')) { j += 2; while (j < n && /\w/.test(src[j])) j++; }
      push('id', src.slice(i, j), line); i = j; continue;
    }
    if (c === ':' && src[i + 1] === ':' && /[A-Za-z_]/.test(src[i + 2] || '')) {
      let j = i + 2; while (j < n && /\w/.test(src[j])) j++; push('id', src.slice(i, j), line); i = j; continue;
    }
    if (/[0-9]/.test(c) || (c === '.' && /[0-9]/.test(src[i + 1] || ''))) {
      let j = i; while (j < n && /[0-9.]/.test(src[j])) j++;
      if (/[eE]/.test(src[j] || '')) { j++; if (/[+-]/.test(src[j])) j++; while (/[0-9]/.test(src[j] || '')) j++; }
      push('num', src.slice(i, j), line); i = j; continue;
    }
    if (c === '&' && /[A-Za-z_:]/.test(src[i + 1] || '')) {               // &fn / &ns::fn
      let j = i + 1; while (j < n && /[\w:]/.test(src[j])) j++; push('fref', src.slice(i, j), line); i = j; continue;
    }
    if (c === '%' && /[A-Za-z_]/.test(src[i + 1] || '')) {               // %xanim (not the modulo operator)
      const p = toks[toks.length - 1];
      const prevIsValue = p && ((p.t === 'id' && !KEYWORDS.has(p.v.toLowerCase())) || p.t === 'num' || p.v === ')' || p.v === ']');
      if (!prevIsValue) { let j = i + 1; while (j < n && /\w/.test(src[j])) j++; push('anim', src.slice(i, j), line); i = j; continue; }
    }
    const three = src.substr(i, 3), two = src.substr(i, 2);
    if (three === '<<=' || three === '>>=') { push('op', three, line); i += 3; continue; }
    if (['==', '!=', '<=', '>=', '&&', '||', '++', '--', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<', '>>'].includes(two)) { push('op', two, line); i += 2; continue; }
    push('op', c, line); i++;
  }
  return toks;
}

function lintSource(file, src) {
  const toks = tokenize(src);
  const hits = [];
  const hit = (rule, line, msg) => hits.push({ file, rule, line, msg });

  let blocker = null;
  for (const t of toks) {
    if (t.t === 'dir') {
      if (t.v === 'using' && blocker) hit('DIRECTIVE', t.line, '#using after ' + blocker);
      if ((t.v === 'precache' || t.v === 'namespace') && !blocker) blocker = '#' + t.v + ' (line ' + t.line + ')';
    } else if (t.t === 'id' && t.v === 'function' && !blocker) blocker = 'the first function (line ' + t.line + ')';
  }

  const code = toks.filter(t => t.t !== 'dir');
  const stack = [];
  for (let k = 0; k < code.length; k++) {
    const t = code[k];
    if (t.t !== 'op') continue;
    if (t.v === '(') {
      const p = k > 0 ? code[k - 1] : null;
      let type = 'group';
      if (p && p.t === 'id') type = STMT_PAREN.has(p.v.toLowerCase()) ? 'stmt' : (KEYWORDS.has(p.v.toLowerCase()) ? 'group' : 'call');
      else if (p && (p.v === ')' || p.v === ']')) type = 'call';
      stack.push({ ch: '(', type, line: t.line });
    } else if (t.v === '[' || t.v === '{') {
      stack.push({ ch: t.v, type: t.v, line: t.line });
    } else if (t.v === ')' || t.v === ']' || t.v === '}') {
      const want = { ')': '(', ']': '[', '}': '{' }[t.v];
      const top = stack.pop();
      if (!top || top.ch !== want) {
        hit('BALANCE', t.line, 'unmatched ' + t.v + (top ? ' (open ' + top.ch + ' at line ' + top.line + ')' : ''));
        if (top) stack.push(top);
        continue;
      }
      if (t.v === ')' && top.type === 'group') {
        const nx = code[k + 1], nx2 = code[k + 2];
        if (nx && nx.v === '.' && nx2 && nx2.t === 'id') hit('PAREN_FIELD', t.line, '( expr ).' + nx2.v);
      }
    } else if (t.v === '?') {
      const top = stack[stack.length - 1];
      if (!top) hit('TERNARY', t.line, 'a ternary outside any paren - write ( c ? a : b )');
      else if (top.ch !== '(' || top.type !== 'group') {
        hit('TERNARY', t.line, 'a ternary not wrapped in its own parens (innermost: ' + (top.ch === '(' ? top.type + ' paren' : top.ch) +
          ' from line ' + top.line + ') - write ( c ? a : b )');
      }
    }
  }
  for (const s of stack) hit('BALANCE', s.line, 'unclosed ' + s.ch);

  let depth = 0;
  for (let k = 0; k < code.length; k++) {
    const t = code[k];
    if (t.t === 'op' && t.v === '{') depth++;
    else if (t.t === 'op' && t.v === '}') depth--;
    else if (depth === 0 && t.t === 'id' && code[k + 1] && code[k + 1].v === '(') {
      let d = 0, j = k + 1;
      for (; j < code.length; j++) { if (code[j].v === '(') d++; else if (code[j].v === ')') { d--; if (d === 0) break; } }
      if (code[j + 1] && code[j + 1].v === '{') {
        const b1 = code[k - 1], b2 = code[k - 2];
        const ok = (b1 && b1.v === 'function') || (b1 && (b1.v === 'private' || b1.v === 'autoexec') && b2 && b2.v === 'function');
        if (!ok) hit('NO_FUNCTION', t.line, t.v + '( ... ) { without the function keyword');
      }
    }
  }

  for (let k = 0; k < code.length; k++) {
    if (!(code[k].t === 'id' && code[k].v === 'function')) continue;
    let j = k + 1;
    while (code[j] && (code[j].v === 'private' || code[j].v === 'autoexec')) j++;
    const name = code[j];
    if (!name || !code[j + 1] || code[j + 1].v !== '(') continue;
    const defined = new Set();
    let d = 0, p = j + 1, expectName = true;
    for (; p < code.length; p++) {
      const t = code[p];
      if (t.v === '(') { d++; if (d === 1) { expectName = true; continue; } }
      if (t.v === ')') { d--; if (d === 0) break; }
      if (d === 1 && t.v === ',') { expectName = true; continue; }
      if (d === 1 && expectName && t.t === 'id') { defined.add(t.v.toLowerCase()); expectName = false; }
    }
    const b = p + 1;
    if (!code[b] || code[b].v !== '{') continue;
    let dd = 0, e = b;
    for (; e < code.length; e++) { if (code[e].v === '{') dd++; else if (code[e].v === '}') { dd--; if (dd === 0) break; } }
    const body = code.slice(b, e + 1);
    for (let q = 0; q < body.length; q++) {
      const t = body[q], prev = body[q - 1], next = body[q + 1];
      if (t.t !== 'id') continue;
      const low = t.v.toLowerCase();
      const isField = prev && prev.v === '.';
      if (next && next.t === 'op' && ASSIGN_OPS.has(next.v) && !isField) defined.add(low);
      if (next && next.v === '[' && !isField) {
        let bd = 0, r = q + 1;
        for (; r < body.length; r++) { if (body[r].v === '[') bd++; else if (body[r].v === ']') { bd--; if (bd === 0) break; } }
        if (body[r + 1] && body[r + 1].v === '=') defined.add(low);
      }
      if (low === 'foreach' && next && next.v === '(') {
        for (let r = q + 2; r < body.length && body[r].v !== 'in'; r++) if (body[r].t === 'id') defined.add(body[r].v.toLowerCase());
      }
      if ((low === 'waittill' || low === 'waittillmatch') && next && next.v === '(') {
        let wd = 0, commas = 0;
        for (let r = q + 1; r < body.length; r++) {
          const u = body[r];
          if (u.v === '(') wd++;
          else if (u.v === ')') { wd--; if (wd === 0) break; }
          else if (wd === 1 && u.v === ',') commas++;
          else if (wd === 1 && commas >= (low === 'waittillmatch' ? 2 : 1) && u.t === 'id') defined.add(u.v.toLowerCase());
        }
      }
    }
    const reported = new Set();
    for (let q = 1; q < body.length; q++) {
      const t = body[q], prev = body[q - 1], next = body[q + 1];
      if (t.t !== 'id') continue;
      const low = t.v.toLowerCase();
      if (KEYWORDS.has(low) || defined.has(low) || t.v.includes('::')) continue;
      if (/^[A-Z0-9_]+$/.test(t.v) && /[A-Z]/.test(t.v)) continue;
      if (prev && prev.v === '.') continue;
      if (next && next.v === '(') continue;
      if (reported.has(low)) continue;
      reported.add(low);
      hit('UNINIT', t.line, name.v + '(): reads "' + t.v + '" which this function never assigns');
    }
    k = e;
  }
  return hits;
}

// ---- the self-test: each bad shape must be caught, each good shape must stay clean -----------------------------
const FIXTURE = [
  '#using scripts\\shared\\util_shared;',          // 1
  '#insert scripts\\shared\\shared.gsh;',          // 2
  '#using scripts\\shared\\callbacks_shared;',     // 3  ok: a #using after an #insert compiles
  '#namespace fixture;',                           // 4
  '#using scripts\\shared\\array_shared;',         // 5  DIRECTIVE
  '',                                              // 6
  'function good( a, b )',                         // 7
  '{',                                             // 8
  '\tx = ( ( a > 1 ) ? 2 : 3 );',                  // 9  ok
  '\tself SetModel( ( ( a > 1 ) ? "x" : "y" ) );', // 10 ok
  '\tself waittill( "damage", amount, attacker );',// 11 ok: waittill assigns
  '\tforeach ( k, v in level.things ) x += v;',    // 12 ok: foreach assigns
  '\tself UseAnimTree( #animtree );',              // 13 ok: a mid-line # is a value
  '\tself AnimScripted( "n", self.origin, self.angles, %xanim_a );', // 14 ok
  '\treturn ( a ? amount : attacker.health ) + b % 2 + IS_TRUE( x );', // 15 ok
  '}',                                             // 16
  '',                                              // 17
  'function bad( a )',                             // 18
  '{',                                             // 19
  '\tself SetModel( ( a > 1 ) ? "x" : "y" );',     // 20 TERNARY (call args: build 6)
  '\ty = a ? 1 : 2;',                              // 21 TERNARY (bare)
  '\tz = y[ a ? 0 : 1 ];',                          // 22 TERNARY ([ ])
  '\tw = ( a ).origin;',                           // 23 PAREN_FIELD
  '\treturn w + c;',                               // 24 UNINIT c
  '}',                                             // 25
  '',                                              // 26
  'no_keyword( a )',                               // 27 NO_FUNCTION
  '{',                                             // 28
  '\treturn ( a;',                                 // 29 BALANCE
  '}',                                             // 30
].join('\n');
const EXPECT = ['DIRECTIVE:5', 'TERNARY:20', 'TERNARY:21', 'TERNARY:22', 'PAREN_FIELD:23', 'UNINIT:24', 'NO_FUNCTION:27', 'BALANCE:'];

function selftest() {
  const got = lintSource('selftest', FIXTURE);
  const keys = got.map(h => h.rule + ':' + h.line);
  const problems = [];
  for (const e of EXPECT) if (!keys.some(k => k.startsWith(e))) problems.push('missed ' + e);
  for (const h of got) if (h.line >= 7 && h.line <= 16) problems.push('false positive in the clean function: ' + h.rule + ':' + h.line + ' ' + h.msg);
  if (keys.some(k => k === 'DIRECTIVE:3')) problems.push('false positive: a #using after an #insert');
  return problems;
}

function walk(dir, out) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out); else if (/\.(gsc|csc)$/i.test(e.name)) out.push(p);
  }
  return out;
}

function main() {
  const args = process.argv.slice(2);
  const st = selftest();
  if (st.length) { for (const p of st) console.log('SELFTEST FAIL: ' + p); console.log('GSC STRICT LINT: the self-test failed; the lint cannot be trusted'); process.exit(1); }
  if (args.includes('--selftest')) { console.log('GSC STRICT LINT SELFTEST OK: ' + EXPECT.length + ' planted errors caught, the clean shapes stay clean'); return; }
  const root = path.resolve(__dirname, '..');
  const files = args.length ? args : walk(path.join(root, 'scripts'), []);
  let hits = [];
  for (const f of files) hits = hits.concat(lintSource(path.relative(root, path.resolve(f)).replace(/\\/g, '/'), fs.readFileSync(f, 'utf8')));
  for (const h of hits) console.log(`${h.file}:${h.line}  ${h.rule}  ${h.msg}`);
  if (hits.length) {
    console.log(`GSC STRICT LINT FAILED: ${hits.length} hit(s) in ${files.length} script(s) - the linker would stop at the first ` +
      'with "No generated data" after the whole build. Fix the script (rules in tools/lint_tod_gsc_strict.js).');
    process.exit(1);
  }
  console.log(`GSC STRICT LINT OK: ${files.length} scripts - no unwrapped ternary, ( expr ).field, late #using, keyword-less ` +
    'function, never-assigned local or unbalanced bracket (self-test: ' + EXPECT.length + ' planted errors caught)');
}

if (require.main === module) main();
module.exports = { lintSource, tokenize, selftest };
