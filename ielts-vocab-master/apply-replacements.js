// Reusable utility: replace specific word-entry objects inside ALL_PARTS by catId + wordIndex.
// Usage: node apply-replacements.js replacements.json
const fs = require("fs");

const HTML_PATH = "vocab-master.html";
const replacementsPath = process.argv[2];
if (!replacementsPath) {
  console.error("Usage: node apply-replacements.js <replacements.json>");
  process.exit(1);
}
const replacements = JSON.parse(fs.readFileSync(replacementsPath, "utf8"));
// replacements: [{ catId, wordIndex, oldWord, newWord: {w,pos,cefr,def,syn,ant,ex} }]

const html = fs.readFileSync(HTML_PATH, "utf8");

const startMarker = "const ALL_PARTS = [";
const startIdx = html.indexOf(startMarker);
const arrOpenIdx = startIdx + startMarker.length - 1; // index of '['
let i = arrOpenIdx + 1;
let depth = 1;
while (depth > 0) {
  if (html[i] === "[") depth++;
  else if (html[i] === "]") depth--;
  i++;
}
const arrCloseIdx = i - 1; // index of ']'

// Parse category object spans within ALL_PARTS
function parseObjectSpans(text, openChar, closeChar, startOffset) {
  const spans = [];
  let d = 0;
  let spanStart = -1;
  for (let p = 0; p < text.length; p++) {
    const ch = text[p];
    if (ch === openChar) {
      if (d === 0) spanStart = p;
      d++;
    } else if (ch === closeChar) {
      d--;
      if (d === 0) {
        spans.push([spanStart + startOffset, p + 1 + startOffset]);
      }
    }
  }
  return spans;
}

const allPartsInner = html.slice(arrOpenIdx + 1, arrCloseIdx);
const catSpans = parseObjectSpans(allPartsInner, "{", "}", arrOpenIdx + 1);
console.log("Categories found:", catSpans.length);

function escapeForJs(str) {
  return str.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

function serializeWord(w) {
  const synStr = JSON.stringify(w.syn || []);
  const antStr = JSON.stringify(w.ant || []);
  return `{ w: "${escapeForJs(w.w)}", pos: "${escapeForJs(w.pos)}", cefr: "${escapeForJs(w.cefr)}", def: "${escapeForJs(w.def)}", syn: ${synStr}, ant: ${antStr}, ex: "${escapeForJs(w.ex)}" }`;
}

// Build catId -> span lookup by reading each category's id field
const catInfo = catSpans.map(([s, e]) => {
  const text = html.slice(s, e);
  const m = text.match(/id:\s*"([^"]+)"/);
  return { id: m ? m[1] : null, start: s, end: e, text };
});

const pendingReplacements = []; // {start, end, newText}
let notFound = [];

for (const rep of replacements) {
  const cat = catInfo.find((c) => c.id === rep.catId);
  if (!cat) {
    notFound.push(rep);
    continue;
  }
  // find words array within this category's text (spacing varies: "words: [" or "words:[")
  const wordsMatch = cat.text.match(/words:\s*\[/);
  if (!wordsMatch) {
    notFound.push(rep);
    continue;
  }
  const wordsArrOpen = wordsMatch.index + wordsMatch[0].length - 1; // index of '[' relative to cat.text
  const wordsInner = cat.text.slice(wordsArrOpen + 1); // rest of cat text after '['
  // parse word object spans relative to wordsArrOpen+1 (relative to cat.text)
  const wordSpansRel = parseObjectSpans(wordsInner, "{", "}", wordsArrOpen + 1);
  if (rep.wordIndex >= wordSpansRel.length) {
    notFound.push(rep);
    continue;
  }
  const [relStart, relEnd] = wordSpansRel[rep.wordIndex];
  const absStart = cat.start + relStart;
  const absEnd = cat.start + relEnd;
  const actualText = html.slice(absStart, absEnd);
  const wMatch = actualText.match(/w:\s*"([^"]+)"/);
  const actualWord = wMatch ? wMatch[1] : null;
  if (rep.oldWord && actualWord && actualWord.toLowerCase() !== rep.oldWord.toLowerCase()) {
    console.log(`MISMATCH for ${rep.catId}[${rep.wordIndex}]: expected "${rep.oldWord}" found "${actualWord}"`);
    notFound.push(rep);
    continue;
  }
  pendingReplacements.push({ start: absStart, end: absEnd, newText: serializeWord(rep.newWord), catId: rep.catId, wordIndex: rep.wordIndex, oldWord: actualWord });
}

console.log("Replacements matched:", pendingReplacements.length, "/ Not found:", notFound.length);
if (notFound.length) {
  console.log("NOT FOUND DETAILS:", JSON.stringify(notFound.slice(0, 10), null, 2));
}

// Apply replacements from the end of the file backwards so offsets remain valid
pendingReplacements.sort((a, b) => b.start - a.start);
let newHtml = html;
for (const r of pendingReplacements) {
  newHtml = newHtml.slice(0, r.start) + r.newText + newHtml.slice(r.end);
}

fs.writeFileSync(HTML_PATH, newHtml);
console.log("Applied", pendingReplacements.length, "replacements. File updated.");
