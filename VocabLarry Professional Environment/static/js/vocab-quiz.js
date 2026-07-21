(function(){
  var FAMILIES = ["quiz", "gap", "challenge"];
  var FAMILY_LABELS = { quiz: "Quiz", gap: "Fill the Gap", challenge: "Challenge" };

  var QUIZ_MODES = [
    { id: "definition", name: "Definition Match", desc: "See a word — choose its correct definition." },
    { id: "word", name: "Word from Definition", desc: "Read a definition — choose the matching word." },
    { id: "synonym", name: "Synonym Match", desc: "See a word — choose a word with a similar meaning." },
    { id: "antonym", name: "Antonym Match", desc: "See a word — choose a word with the opposite meaning." },
    { id: "mixed", name: "Mixed Review", desc: "A random mix of every question type." }
  ];

  var GAP_MODES = [
    { id: "gap-context", name: "Contextual Definition", desc: "The sentence provides context clues — use them to find the missing word." },
    { id: "gap-nuance", name: "Lexical Nuance", desc: "Near-synonyms are the distractors — only one word is precisely correct." },
    { id: "gap-collocation", name: "Collocation & Idiom", desc: "The blank requires a specific fixed word partnership or collocation." },
    { id: "gap-connotation", name: "Connotation Match", desc: "Choose the word whose tone — positive, negative or formal — fits the sentence." },
    { id: "gap-mixed", name: "Mixed Review", desc: "A random mix of all four gap fill types." }
  ];

  function initSetupPage(){
    var form = document.getElementById("quizSetupForm");
    if (!form) return;

    var modeInput = document.getElementById("modeInput");
    var cefrInput = document.getElementById("cefrInput");
    var countInput = document.getElementById("countInput");
    var familyLabel = document.getElementById("familyLabel");
    var quizGrid = document.getElementById("quizModeGrid");
    var gapGrid = document.getElementById("gapModeGrid");
    var countRow = document.getElementById("countRow");
    var customChip = document.getElementById("customCountChip");
    var customInput = document.getElementById("customCountInput");
    var customWarn = document.getElementById("customCountWarn");

    var familyIdx = 0;

    function renderModeGrid(container, modes){
      container.innerHTML = modes.map(function(m, i){
        return '<button type="button" class="modeCard' + (i === 0 ? ' active' : '') + '" data-mode="' + m.id + '">' +
          '<h3>' + m.name + '</h3><p>' + m.desc + '</p></button>';
      }).join("");
      container.querySelectorAll(".modeCard").forEach(function(card){
        card.addEventListener("click", function(){
          container.querySelectorAll(".modeCard").forEach(function(c){ c.classList.remove("active"); });
          card.classList.add("active");
          modeInput.value = card.dataset.mode;
        });
      });
    }

    function applyFamily(){
      var family = FAMILIES[familyIdx];
      familyLabel.textContent = FAMILY_LABELS[family];
      quizGrid.hidden = family !== "quiz";
      gapGrid.hidden = family !== "gap";
      if (family === "quiz"){
        modeInput.value = QUIZ_MODES[0].id;
      } else if (family === "gap"){
        modeInput.value = GAP_MODES[0].id;
      } else {
        modeInput.value = "challenge";
      }
    }

    renderModeGrid(quizGrid, QUIZ_MODES);
    renderModeGrid(gapGrid, GAP_MODES);

    document.getElementById("familyPrev").addEventListener("click", function(){
      familyIdx = (familyIdx - 1 + FAMILIES.length) % FAMILIES.length;
      applyFamily();
    });
    document.getElementById("familyNext").addEventListener("click", function(){
      familyIdx = (familyIdx + 1) % FAMILIES.length;
      applyFamily();
    });
    applyFamily();

    form.querySelectorAll(".chip[data-quiz-cefr]").forEach(function(chip){
      chip.addEventListener("click", function(){
        form.querySelectorAll(".chip[data-quiz-cefr]").forEach(function(c){ c.classList.remove("active"); });
        chip.classList.add("active");
        cefrInput.value = chip.dataset.quizCefr === "all" ? "" : chip.dataset.quizCefr;
      });
    });

    function setCount(value){
      countInput.value = value;
      countRow.querySelectorAll(".chip[data-count]").forEach(function(c){
        c.classList.toggle("active", c.dataset.count === String(value));
      });
      customChip.classList.remove("active");
      customInput.hidden = true;
      customWarn.style.display = "none";
    }

    countRow.querySelectorAll(".chip[data-count]").forEach(function(chip){
      chip.addEventListener("click", function(){ setCount(chip.dataset.count); });
    });

    customChip.addEventListener("click", function(){
      countRow.querySelectorAll(".chip[data-count]").forEach(function(c){ c.classList.remove("active"); });
      customChip.classList.add("active");
      customInput.hidden = false;
      customInput.focus();
      var val = parseInt(customInput.value, 10);
      if (val > 0) countInput.value = val;
    });

    customInput.addEventListener("click", function(e){ e.stopPropagation(); });
    customInput.addEventListener("input", function(){
      var val = parseInt(customInput.value, 10);
      if (val > 0){
        customInput.classList.remove("bad");
        customWarn.style.display = "none";
        countInput.value = val;
      } else {
        customInput.classList.add("bad");
        customWarn.style.display = "block";
      }
    });
  }

  initSetupPage();

  var root = document.getElementById("quizPlayRoot");
  if (!root) return;

  var params = new URLSearchParams(window.location.search);
  var categorySlug = params.get("category") || "";
  var cefrCode = params.get("cefr") || "";
  var requestedCount = params.get("count") || "10";
  var mode = params.get("mode") || "definition";

  var state = {
    allWords: [],
    categoriesBySlug: {},
    questions: [],
    idx: 0,
    score: 0,
    answers: [],
  };

  function shuffle(arr){
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--){
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
    }
    return a;
  }

  function capitalize(s){
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
  }

  function buildOptions(correct, othersPool, getValue){
    var opts = [correct];
    var pool = shuffle(othersPool);
    var i = 0;
    while (opts.length < 4 && i < pool.length){
      var candidate = getValue(pool[i]);
      if (candidate && opts.indexOf(candidate) === -1) opts.push(candidate);
      i++;
    }
    return shuffle(opts);
  }

  function randomMixedMode(word){
    var options = ["definition", "word"];
    if (word.synonyms && word.synonyms.length) options.push("synonym");
    if (word.antonyms && word.antonyms.length) options.push("antonym");
    return options[Math.floor(Math.random() * options.length)];
  }

  function buildQuestion(word, qMode){
    var others = state.allWords.filter(function(w){ return w.id !== word.id; });
    var prompt, text, correct, options;
    if (qMode === "word"){
      prompt = "Which word matches this definition?";
      text = word.definition;
      correct = word.word;
      options = buildOptions(correct, others, function(w){ return w.word; });
    } else if (qMode === "synonym"){
      var syns = word.synonyms || [];
      correct = capitalize(syns[Math.floor(Math.random() * syns.length)]);
      prompt = "Choose a word with a similar meaning:";
      text = word.word + " (" + word.pos + ")";
      options = buildOptions(correct, others.filter(function(w){ return w.word !== correct; }), function(w){ return w.word; });
    } else if (qMode === "antonym"){
      var ants = word.antonyms || [];
      correct = capitalize(ants[Math.floor(Math.random() * ants.length)]);
      prompt = "Choose a word with the opposite meaning:";
      text = word.word + " (" + word.pos + ")";
      options = buildOptions(correct, others.filter(function(w){ return w.word !== correct; }), function(w){ return w.word; });
    } else {
      prompt = "Choose the correct definition:";
      text = word.word + " (" + word.pos + ")";
      correct = word.definition;
      options = buildOptions(correct, others, function(w){ return w.definition; });
    }
    return { prompt: prompt, text: text, options: options, correct: correct, word: word };
  }

  var GAP_PROMPTS = {
    context: "Choose the word that best completes the sentence.",
    nuance: "Near-synonyms are the options — only one word is precisely correct.",
    collocation: "The blank requires a specific fixed word partnership.",
    connotation: "Choose the word whose tone fits the sentence."
  };

  function stripEmTags(s){
    return (s || "").replace(/<\/?em>/g, "");
  }

  function buildGapQuestion(word, gapMode){
    if (gapMode === "gap-mixed"){
      var concrete = ["gap-context", "gap-nuance", "gap-collocation", "gap-connotation"];
      return buildGapQuestion(word, concrete[Math.floor(Math.random() * concrete.length)]);
    }
    var others = state.allWords.filter(function(w){ return w.id !== word.id; });
    var samePos = others.filter(function(w){ return w.pos === word.pos; });
    var distractorPool, subMode;
    if (gapMode === "gap-nuance"){
      subMode = "nuance";
      var synSet = {};
      (word.synonyms || []).forEach(function(s){ synSet[s.toLowerCase()] = true; });
      var synPool = others.filter(function(w){
        return w.synonyms && w.synonyms.some(function(s){ return synSet[s.toLowerCase()]; });
      });
      distractorPool = synPool.length >= 3 ? synPool : samePos;
    } else if (gapMode === "gap-collocation"){
      subMode = "collocation";
      var sameCat = others.filter(function(w){ return w.category_id === word.category_id; });
      distractorPool = sameCat.length >= 3 ? sameCat : samePos;
    } else if (gapMode === "gap-connotation"){
      subMode = "connotation";
      var antSet = {};
      (word.antonyms || []).forEach(function(a){ antSet[a.toLowerCase()] = true; });
      var antPool = others.filter(function(w){ return antSet[w.word.toLowerCase()]; });
      distractorPool = antPool.length >= 2
        ? antPool.concat(samePos.filter(function(w){ return !antSet[w.word.toLowerCase()]; }))
        : samePos;
    } else {
      subMode = "context";
      distractorPool = samePos.length >= 3 ? samePos : others;
    }
    var options = buildOptions(word.word, distractorPool, function(w){ return w.word; });
    var text = word.gap.replace("___", '<span class="vocab-quiz-blank">_____</span>');
    return {
      type: "gap",
      prompt: GAP_PROMPTS[subMode],
      text: text,
      options: options,
      correct: word.word,
      word: word
    };
  }

  function buildHybridQuestion(word){
    var candidates = ["definition", "word"];
    if (word.synonyms && word.synonyms.length) candidates.push("synonym");
    if (word.antonyms && word.antonyms.length) candidates.push("antonym");
    if (word.gap && word.gap.indexOf("___") !== -1) candidates.push("gap");
    var pick = candidates[Math.floor(Math.random() * candidates.length)];
    if (pick === "gap"){
      var gapSubModes = ["gap-context", "gap-nuance", "gap-collocation", "gap-connotation"];
      return buildGapQuestion(word, gapSubModes[Math.floor(Math.random() * gapSubModes.length)]);
    }
    return buildQuestion(word, pick);
  }

  function buildPool(){
    var pool = state.allWords;
    if (categorySlug){
      var catId = state.categoriesBySlug[categorySlug];
      if (catId) pool = pool.filter(function(w){ return w.category_id === catId; });
    }
    if (cefrCode){
      pool = pool.filter(function(w){ return w.cefr_code === cefrCode; });
    }
    if (mode === "synonym"){
      pool = pool.filter(function(w){ return w.synonyms && w.synonyms.length; });
    } else if (mode === "antonym"){
      pool = pool.filter(function(w){ return w.antonyms && w.antonyms.length; });
    } else if (mode.indexOf("gap-") === 0){
      pool = pool.filter(function(w){ return w.gap && w.gap.indexOf("___") !== -1; });
    }
    return pool;
  }

  function pickTargetWords(pool){
    var shuffled = shuffle(pool);
    if (requestedCount === "all") return shuffled;
    var n = parseInt(requestedCount, 10) || 10;
    return shuffled.slice(0, Math.min(n, shuffled.length));
  }

  function generateQuestions(){
    var pool = buildPool();
    var targets = pickTargetWords(pool);
    state.questions = targets.map(function(word){
      if (mode === "challenge") return buildHybridQuestion(word);
      if (mode.indexOf("gap-") === 0) return buildGapQuestion(word, mode);
      var qMode = mode === "mixed" ? randomMixedMode(word) : mode;
      return buildQuestion(word, qMode);
    });
  }

  function renderError(message){
    root.innerHTML = '<p class="vocab-quiz-error">' + message + ' <a href="/vocabulary/quiz/">Back to setup</a></p>';
  }

  function renderQuestion(){
    var q = state.questions[state.idx];
    var total = state.questions.length;
    var pct = Math.round(((state.idx + 1) / total) * 100);
    root.innerHTML =
      '<div class="vocab-quiz-progress"><div class="vocab-quiz-progress-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="vocab-quiz-meta"><span>Question ' + (state.idx + 1) + ' of ' + total + '</span><span>Score: ' + state.score + '</span></div>' +
      '<div class="vocab-quiz-card">' +
        '<div class="vocab-quiz-prompt">' + q.prompt + '</div>' +
        '<div class="vocab-quiz-text">' + q.text + '</div>' +
        '<div class="vocab-quiz-options">' +
          q.options.map(function(opt){ return '<button type="button" class="vocab-quiz-opt">' + opt + '</button>'; }).join("") +
        '</div>' +
        '<div class="vocab-quiz-feedback"></div>' +
        '<div class="vocab-quiz-next" style="display:none;"><button type="button" class="btn" id="quizNextBtn"></button></div>' +
      '</div>';
    root.querySelectorAll(".vocab-quiz-opt").forEach(function(btn){
      btn.addEventListener("click", function(){ handleAnswer(btn, q); });
    });
  }

  function handleAnswer(selectedBtn, q){
    var isCorrect = selectedBtn.textContent === q.correct;
    root.querySelectorAll(".vocab-quiz-opt").forEach(function(btn){
      btn.disabled = true;
      if (btn.textContent === q.correct) btn.classList.add("correct");
      else if (btn === selectedBtn) btn.classList.add("wrong");
    });
    if (isCorrect) state.score++;
    state.answers.push({ question: q, selected: selectedBtn.textContent, isCorrect: isCorrect });
    var feedback = root.querySelector(".vocab-quiz-feedback");
    var feedbackText = (isCorrect ? "<b>Correct!</b> " : "<b>Not quite.</b> The answer is " + q.correct + ". ") +
      q.word.word + " — " + q.word.definition;
    if (q.type === "gap" && q.word.example){
      feedbackText += "<br>" + stripEmTags(q.word.example);
    }
    feedback.innerHTML = feedbackText;
    root.querySelector(".vocab-quiz-meta span:last-child").textContent = "Score: " + state.score;
    var nextWrap = root.querySelector(".vocab-quiz-next");
    var nextBtn = document.getElementById("quizNextBtn");
    var isLast = state.idx + 1 === state.questions.length;
    nextBtn.textContent = isLast ? "See Results" : "Next Question";
    nextWrap.style.display = "flex";
    nextBtn.addEventListener("click", function(){
      state.idx++;
      if (state.idx < state.questions.length) renderQuestion();
      else renderResults();
    });
  }

  function renderResults(){
    var total = state.questions.length;
    var pct = total > 0 ? Math.round((state.score / total) * 100) : 0;
    root.innerHTML =
      '<div class="vocab-quiz-results">' +
        '<h2>Quiz Complete</h2>' +
        '<div class="vocab-quiz-score">' + state.score + ' / ' + total + '</div>' +
        '<p class="vocab-quiz-pct">' + pct + '%</p>' +
        '<div class="vocab-quiz-result-actions">' +
          '<button type="button" class="btn" id="quizRetryBtn">Try Again</button>' +
          '<button type="button" class="btn" id="quizChangeBtn">Change Settings</button>' +
          '<button type="button" class="btn" id="quizReviewBtn">Review Answers</button>' +
        '</div>' +
        '<div class="vocab-quiz-review" id="quizReview" style="display:none;"></div>' +
      '</div>';
    document.getElementById("quizRetryBtn").addEventListener("click", function(){
      state.idx = 0;
      state.score = 0;
      state.answers = [];
      generateQuestions();
      if (state.questions.length === 0){
        renderError("No words available for this combination — try different settings.");
        return;
      }
      renderQuestion();
    });
    document.getElementById("quizChangeBtn").addEventListener("click", function(){
      window.location.href = "/vocabulary/quiz/";
    });
    document.getElementById("quizReviewBtn").addEventListener("click", function(){
      var panel = document.getElementById("quizReview");
      if (panel.style.display === "block"){ panel.style.display = "none"; return; }
      panel.innerHTML = state.answers.map(function(a, i){
        return '<div class="vocab-quiz-review-item ' + (a.isCorrect ? "correct" : "wrong") + '">' +
          '<span class="vocab-quiz-review-num">' + (i + 1) + '</span>' +
          '<span class="vocab-quiz-review-word">' + a.question.word.word + '</span>' +
          '<span class="vocab-quiz-review-answer">Your answer: ' + a.selected + '</span>' +
          (a.isCorrect ? '' : '<span class="vocab-quiz-review-correct">Correct: ' + a.question.correct + '</span>') +
        '</div>';
      }).join("");
      panel.style.display = "block";
    });
  }

  function init(){
    Promise.all([
      fetch("/api/words/").then(function(r){ return r.json(); }),
      fetch("/api/categories/").then(function(r){ return r.json(); }),
    ]).then(function(results){
      state.allWords = results[0];
      results[1].forEach(function(c){ state.categoriesBySlug[c.slug] = c.id; });
      generateQuestions();
      if (state.questions.length === 0){
        renderError("No words available for this combination — try different settings.");
        return;
      }
      renderQuestion();
    }).catch(function(){
      renderError("Couldn't load quiz data — check your connection and try again.");
    });
  }

  init();
})();
