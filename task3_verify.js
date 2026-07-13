const fs = require('fs');
const html = fs.readFileSync('VocabLarry/vocab-master.html', 'utf-8');

// Simplified jsdom-like behavior for testing CSS display
const pages = [
  'page-list', 'page-examples', 'page-test',
  'page-grammar', 'page-gramword', 'page-gramtest'
];

let allPass = true;
const results = [];

// Test 1: DOM presence - each page has exactly 3 .mobile-page-switcher .chip elements
pages.forEach(pageId => {
  const pageStartRegex = new RegExp(`<section id="${pageId}"`, 'i');
  const pageStartMatch = html.match(pageStartRegex);
  
  if (!pageStartMatch) {
    results.push(`✗ FAIL: ${pageId} not found in DOM`);
    allPass = false;
    return;
  }

  const pageStart = html.indexOf(pageStartMatch[0]);
  const remainingHtml = html.substring(pageStart + 1);
  const nextSectionIdx = remainingHtml.indexOf('<section ');
  const pageEnd = nextSectionIdx !== -1 ? pageStart + 1 + nextSectionIdx : html.length;
  const pageContent = html.substring(pageStart, pageEnd);

  // Find .mobile-page-switcher div and count .chip buttons inside it
  const switcherMatch = pageContent.match(/<div class="mobile-page-switcher">([\s\S]*?)<\/div>/);
  if (!switcherMatch) {
    results.push(`✗ FAIL: ${pageId} has no .mobile-page-switcher`);
    allPass = false;
    return;
  }

  const switcherContent = switcherMatch[1];
  const chipCount = (switcherContent.match(/class="chip"/g) || []).length;

  if (chipCount === 3) {
    results.push(`✓ PASS: ${pageId} has 3 switcher buttons`);
  } else {
    results.push(`✗ FAIL: ${pageId} has ${chipCount} switcher buttons, expected 3`);
    allPass = false;
  }
});

// Test 2: CSS visibility at mobile width
// Check that .mobile-page-switcher{display:flex;} appears directly after the canonical media query opening
const mobileMediaIndex = html.indexOf('@media (max-width:640px){');
let hasMobilePageSwitcher = false;
if (mobileMediaIndex !== -1) {
  // Extract from the media query up to its closing brace
  let braceCount = 1;
  let searchIdx = mobileMediaIndex + '@media (max-width:640px){'.length;
  while (braceCount > 0 && searchIdx < html.length) {
    if (html[searchIdx] === '{') braceCount++;
    if (html[searchIdx] === '}') braceCount--;
    searchIdx++;
  }
  const mediaBlock = html.substring(mobileMediaIndex, searchIdx);
  hasMobilePageSwitcher = mediaBlock.includes('.mobile-page-switcher{display:flex;}');
}

if (hasMobilePageSwitcher) {
  results.push(`✓ PASS: .mobile-page-switcher has display:flex in @media (max-width:640px)`);
} else {
  results.push(`✗ FAIL: .mobile-page-switcher display:flex not found in mobile media query`);
  allPass = false;
}

// Test 3: CSS hidden on desktop
// Check that .mobile-page-switcher{display:none} exists outside media query
const desktopHidden = html.match(/\.mobile-page-switcher\s*{\s*display\s*:\s*none/);
if (desktopHidden) {
  results.push(`✓ PASS: .mobile-page-switcher has display:none on desktop`);
} else {
  results.push(`✗ FAIL: .mobile-page-switcher display:none not found`);
  allPass = false;
}

console.log('\n=== TASK 3 VERIFICATION (COUNT/VISIBILITY) ===\n');
results.forEach(r => console.log(r));
console.log(`\n${allPass ? '✓ ALL TESTS PASSED' : '✗ SOME TESTS FAILED'}\n`);
process.exit(allPass ? 0 : 1);
