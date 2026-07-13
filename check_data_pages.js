const fs = require('fs');
const html = fs.readFileSync('VocabLarry/vocab-master.html', 'utf-8');

// Extract pages and their switcher data-page values
const pages = [
  { id: 'page-list', name: 'Vocabulary: List/Category', expected: ['list', 'examples', 'test'] },
  { id: 'page-examples', name: 'Vocabulary: Examples/Word', expected: ['list', 'examples', 'test'] },
  { id: 'page-test', name: 'Vocabulary: Test/Quiz', expected: ['list', 'examples', 'test'] },
  { id: 'page-grammar', name: 'Grammar: Category', expected: ['grammar', 'gramword', 'gramtest'] },
  { id: 'page-gramword', name: 'Grammar: Reference/Word', expected: ['grammar', 'gramword', 'gramtest'] },
  { id: 'page-gramtest', name: 'Grammar: Test', expected: ['grammar', 'gramword', 'gramtest'] }
];

let allPass = true;
const results = [];

pages.forEach(page => {
  // Find the page section
  const pageStartRegex = new RegExp(`<section id="${page.id}"`, 'i');
  const pageStartMatch = html.match(pageStartRegex);
  
  if (!pageStartMatch) {
    results.push(`✗ FAIL: Page #${page.id} not found`);
    allPass = false;
    return;
  }

  const pageStart = html.indexOf(pageStartMatch[0]);
  // Find the next section tag to bound the search
  const remainingHtml = html.substring(pageStart + 1);
  const nextSectionIdx = remainingHtml.indexOf('<section ');
  const pageEnd = nextSectionIdx !== -1 ? pageStart + 1 + nextSectionIdx : html.length;
  const pageContent = html.substring(pageStart, pageEnd);

  // Find all data-page attributes in button.chip elements
  const chipRegex = /data-page="([^"]+)"/g;
  const actual = [];
  let match;
  while ((match = chipRegex.exec(pageContent)) !== null) {
    actual.push(match[1]);
  }

  const expected = page.expected;
  const matches = actual.length === expected.length && 
                  actual.every((val, idx) => val === expected[idx]);

  if (matches) {
    results.push(`✓ PASS: ${page.name} has correct data-page values: [${actual.join(', ')}]`);
  } else {
    results.push(`✗ FAIL: ${page.name}\n    Expected: [${expected.join(', ')}]\n    Actual:   [${actual.join(', ')}]`);
    allPass = false;
  }
});

console.log('\n=== DATA-PAGE ATTRIBUTE VERIFICATION ===\n');
results.forEach(r => console.log(r));
console.log(`\n${allPass ? '✓ ALL TESTS PASSED' : '✗ SOME TESTS FAILED'}\n`);
process.exit(allPass ? 0 : 1);
