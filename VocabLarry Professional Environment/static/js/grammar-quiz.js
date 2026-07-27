(function(){
  var GRAMTEST_MODES = [
    { id: "mcq", name: "Multichoice", desc: "Pick the correct option." },
    { id: "gap", name: "Fill the Gap", desc: "Type the missing word or form." },
    { id: "transform", name: "Rewrite the Sentence", desc: "Rewrite the sentence as instructed." },
    { id: "mixed", name: "Mixed", desc: "All three question styles shuffled together." }
  ];
  var GRAMTEST_COUNTS = [10, 20, 30, 50, 100];
  var GRAMTEST_MAX = 100;
  var GRAMTEST_TOPICS_PER_PAGE = 10;

  function initGramtestSetup(){
    var startBtn = document.getElementById("gramtestStart");
    if (!startBtn) return;

    var modesGrid = document.getElementById("gramtestModes");
    var countsRow = document.getElementById("gramtestCounts");
    var customWarn = document.getElementById("gramtestCustomWarn");
    var poolCountEl = document.getElementById("gramtestPoolCount");
    var searchInput = document.getElementById("gramtestSearch");
    var sectionChipsRow = document.getElementById("gramtestSectionChips");
    var topicChipsRow = document.getElementById("gramtestTopicChips");
    var topicPagerRow = document.getElementById("gramtestTopicPager");
    var emptyMsg = document.getElementById("gramtestEmpty");

    var gramtest = {
      mode: "mcq", count: 10, customCount: 10,
      topics: {}, search: "", section: "all", cefr: "all", topicPage: 0,
    };
    var allTopics = [];
    var sectionsSeen = [];

    function matchesMode(q){
      return gramtest.mode === "mixed" || q.qtype === gramtest.mode;
    }

    function filteredTopics(){
      return allTopics.filter(function(tp){
        return (gramtest.section === "all" || (tp.section && tp.section.slug === gramtest.section))
          && (gramtest.cefr === "all" || tp.cefr === gramtest.cefr);
      });
    }

    function visibleTopics(){
      var needle = gramtest.search.trim().toLowerCase();
      return filteredTopics().filter(function(tp){
        return !needle || tp.title.toLowerCase().indexOf(needle) !== -1;
      });
    }

    function pool(){
      var eligible = filteredTopics().filter(function(tp){
        var selectedCount = Object.keys(gramtest.topics).length;
        return !selectedCount || gramtest.topics[tp.slug];
      });
      var qs = [];
      eligible.forEach(function(tp){
        tp.quiz.forEach(function(q){ if (matchesMode(q)) qs.push(q); });
      });
      return qs;
    }

    function renderModes(){
      modesGrid.innerHTML = GRAMTEST_MODES.map(function(m){
        return '<button type="button" class="modeCard' + (gramtest.mode === m.id ? ' active' : '') + '" data-mode="' + m.id + '">' +
          '<h3>' + m.name + '</h3><p>' + m.desc + '</p></button>';
      }).join("");
      modesGrid.querySelectorAll(".modeCard").forEach(function(card){
        card.addEventListener("click", function(){
          gramtest.mode = card.dataset.mode;
          renderModes();
          renderFilters();
        });
      });
    }

    function renderCounts(){
      var isCustom = gramtest.count === "custom";
      var html = GRAMTEST_COUNTS.map(function(c){
        return '<button type="button" class="chip' + (gramtest.count === c ? ' active' : '') + '" data-count="' + c + '">' + c + ' questions</button>';
      }).join("");
      html += '<span class="custom-chip' + (isCustom ? ' active' : '') + '" id="gramtestCustomChip">' +
        '<span>Custom</span>' +
        '<input type="number" min="1" max="' + GRAMTEST_MAX + '" class="custom-count-input" id="gramtestCustomCount" value="' + gramtest.customCount + '"' + (isCustom ? '' : ' hidden') + '>' +
        '</span>';
      countsRow.innerHTML = html;
      countsRow.querySelectorAll(".chip[data-count]").forEach(function(btn){
        btn.addEventListener("click", function(){
          gramtest.count = parseInt(btn.dataset.count, 10);
          renderCounts();
        });
      });
      var customChip = document.getElementById("gramtestCustomChip");
      var customInput = document.getElementById("gramtestCustomCount");
      customChip.addEventListener("click", function(){
        gramtest.count = "custom";
        renderCounts();
        var freshInput = document.getElementById("gramtestCustomCount");
        if (freshInput) freshInput.focus();
      });
      customInput.addEventListener("click", function(e){ e.stopPropagation(); });
      customInput.addEventListener("input", function(){
        var val = parseInt(customInput.value, 10);
        if (val > 0){
          gramtest.customCount = Math.min(val, GRAMTEST_MAX);
          customInput.classList.remove("bad");
          customWarn.style.display = "none";
        } else {
          customInput.classList.add("bad");
          customWarn.style.display = "block";
        }
      });
    }

    function renderFilters(){
      document.querySelectorAll("[data-gramtest-cefr]").forEach(function(chip){
        chip.classList.toggle("active", chip.dataset.gramtestCefr === gramtest.cefr);
      });

      sectionChipsRow.innerHTML =
        '<button type="button" class="chip' + (gramtest.section === "all" ? ' active' : '') + '" data-section="all">All</button>' +
        sectionsSeen.map(function(sec){
          return '<button type="button" class="chip' + (gramtest.section === sec.slug ? ' active' : '') + '" data-section="' + sec.slug + '">' + sec.name + '</button>';
        }).join("");
      sectionChipsRow.querySelectorAll(".chip[data-section]").forEach(function(btn){
        btn.addEventListener("click", function(){
          gramtest.section = btn.dataset.section;
          gramtest.topics = {};
          gramtest.topicPage = 0;
          renderFilters();
        });
      });

      var visible = visibleTopics();
      var totalTopicPages = Math.max(1, Math.ceil(visible.length / GRAMTEST_TOPICS_PER_PAGE));
      if (gramtest.topicPage >= totalTopicPages) gramtest.topicPage = totalTopicPages - 1;
      if (gramtest.topicPage < 0) gramtest.topicPage = 0;
      var pageTopics = visible.slice(
        gramtest.topicPage * GRAMTEST_TOPICS_PER_PAGE,
        (gramtest.topicPage + 1) * GRAMTEST_TOPICS_PER_PAGE
      );
      topicChipsRow.innerHTML =
        '<button type="button" class="chip' + (Object.keys(gramtest.topics).length === 0 ? ' active' : '') + '" data-all-topics>All Topics</button>' +
        pageTopics.map(function(tp){
          var icon = tp.section && tp.section.icon
            ? '<svg class="ico" aria-hidden="true"><use href="#' + tp.section.icon + '"/></svg> '
            : '';
          return '<button type="button" class="chip ' + (tp.theme || 't-tv') + '"' +
            (gramtest.topics[tp.slug] ? ' data-active="1"' : '') +
            ' data-topic="' + tp.slug + '">' + icon + tp.title + '</button>';
        }).join("");
      topicChipsRow.querySelectorAll(".chip[data-topic]").forEach(function(btn){
        if (btn.dataset.active) btn.classList.add("active");
        btn.addEventListener("click", function(){
          var slug = btn.dataset.topic;
          if (gramtest.topics[slug]) delete gramtest.topics[slug];
          else gramtest.topics[slug] = true;
          renderFilters();
        });
      });
      var allTopicsBtn = topicChipsRow.querySelector("[data-all-topics]");
      allTopicsBtn.addEventListener("click", function(){
        gramtest.topics = {};
        renderFilters();
      });

      if (totalTopicPages > 1){
        topicPagerRow.style.display = "";
        topicPagerRow.innerHTML =
          '<button type="button" class="page-btn' + (gramtest.topicPage === 0 ? ' disabled' : '') + '" id="gramtestTopicPrev">‹ Prev</button>' +
          '<span class="filter-label" style="text-transform:none;">Page ' + (gramtest.topicPage + 1) + ' / ' + totalTopicPages + '</span>' +
          '<button type="button" class="page-btn' + (gramtest.topicPage === totalTopicPages - 1 ? ' disabled' : '') + '" id="gramtestTopicNext">Next ›</button>';
        document.getElementById("gramtestTopicPrev").addEventListener("click", function(){
          gramtest.topicPage--;
          renderFilters();
        });
        document.getElementById("gramtestTopicNext").addEventListener("click", function(){
          gramtest.topicPage++;
          renderFilters();
        });
      } else {
        topicPagerRow.style.display = "none";
        topicPagerRow.innerHTML = "";
      }

      var currentPool = pool();
      poolCountEl.textContent = currentPool.length + " question" + (currentPool.length === 1 ? "" : "s") + " in pool";
      startBtn.disabled = !currentPool.length;
      emptyMsg.style.display = currentPool.length ? "none" : "block";
    }

    document.querySelectorAll("[data-gramtest-cefr]").forEach(function(chip){
      chip.addEventListener("click", function(){
        gramtest.cefr = chip.dataset.gramtestCefr;
        gramtest.topicPage = 0;
        renderFilters();
      });
    });

    searchInput.addEventListener("input", function(){
      gramtest.search = searchInput.value;
      gramtest.topicPage = 0;
      renderFilters();
    });

    document.getElementById("gramtestClearFilters").addEventListener("click", function(){
      gramtest.search = "";
      gramtest.section = "all";
      gramtest.cefr = "all";
      gramtest.topics = {};
      gramtest.topicPage = 0;
      searchInput.value = "";
      renderFilters();
    });

    startBtn.addEventListener("click", function(){
      var currentPool = pool();
      if (!currentPool.length) return;
      var params = new URLSearchParams();
      params.set("qtype", gramtest.mode);
      var wanted = gramtest.count === "custom" ? Math.max(1, gramtest.customCount || 1) : gramtest.count;
      params.set("count", String(Math.min(wanted, GRAMTEST_MAX, currentPool.length)));
      if (gramtest.section !== "all") params.set("section", gramtest.section);
      if (gramtest.cefr !== "all") params.set("cefr", gramtest.cefr);
      var selectedTopics = Object.keys(gramtest.topics);
      if (selectedTopics.length) params.set("topics", selectedTopics.join(","));
      window.location.href = "/grammar/quiz/play/?" + params.toString();
    });

    fetch("/api/grammar/").then(function(r){ return r.json(); }).then(function(stages){
      allTopics = [];
      var seenSlugs = {};
      stages.forEach(function(stage){
        stage.topics.forEach(function(tp){
          allTopics.push(tp);
          if (tp.section && !seenSlugs[tp.section.slug]){
            seenSlugs[tp.section.slug] = true;
            sectionsSeen.push(tp.section);
          }
        });
      });
      renderModes();
      renderCounts();
      renderFilters();
    }).catch(function(){
      poolCountEl.textContent = "";
      startBtn.disabled = true;
      emptyMsg.style.display = "block";
    });
  }

  initGramtestSetup();

  var root = document.getElementById("grammarQuizRoot");
  if (!root) return;

  var topicSlug = root.dataset.topicSlug || null;
  var testMode = root.dataset.mode === "test";
  var DRAW_COUNT = 10;
  var PASS_PCT = 80;

  var state = {
    mode: testMode ? "test" : "topic",
    topic: null,
    pool: [],
    drawCount: DRAW_COUNT,
    questions: [],
    idx: 0,
    score: 0,
  };

  function shuffle(arr){
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--){
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = a[i]; a[i] = a[j]; a[j] = tmp;
    }
    return a;
  }

  function grammarNorm(s){
    return String(s).replace(/[‘’]/g, "'").trim();
  }

  function expectedAnswers(q){
    if (q.qtype !== "gap" || q.prompt.indexOf("___") !== 0) return q.answers;
    return q.answers.map(function(a){
      return a.charAt(0).toUpperCase() + a.slice(1);
    });
  }

  function blankMeansNoAnswer(q){
    return q.qtype === "gap" && q.answers.some(function(a){
      return /^\(?no article\)?$|^-$/i.test(grammarNorm(a));
    });
  }

  function offersBlankGap(){
    return state.questions.some(function(qq){ return blankMeansNoAnswer(qq); });
  }

  function drawQuestions(){
    return shuffle(state.pool).slice(0, state.drawCount);
  }

  function getCsrfToken(){
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function syncMastery(pct){
    fetch("/auth/sync/", { credentials: "same-origin" })
      .then(function(res){ return res.json(); })
      .then(function(data){
        var grammarMap = data.grammar_map || {};
        var learnMap = data.learn_map || {};
        var prev = grammarMap[topicSlug] || { best: 0, done: false };
        var best = Math.max(prev.best, pct);
        grammarMap[topicSlug] = { best: best, done: prev.done || best >= PASS_PCT };
        return fetch("/auth/sync/", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          body: JSON.stringify({ grammar_map: grammarMap, learn_map: learnMap }),
        });
      })
      .catch(function(){
        // Best-effort: the results screen is already rendered and fully
        // usable regardless of whether the sync round-trip succeeds.
      });
  }

  function backHref(){
    return state.mode === "test" ? "/grammar/quiz/" : ("/grammar/category/" + topicSlug + "/");
  }

  function renderError(message){
    var label = state.mode === "test" ? "Back to Test setup" : "Back to topic";
    root.innerHTML = '<p class="grammar-quiz-error">' + message +
      ' <a href="' + backHref() + '">' + label + '</a></p>';
  }

  function renderQuestion(){
    var q = state.questions[state.idx];
    var total = state.questions.length;
    var pct = Math.round(((state.idx + 1) / total) * 100);
    var isTyped = q.qtype !== "mcq";
    var promptLabel = q.qtype === "mcq" ? "Choose the correct option"
      : q.qtype === "gap" ? "Fill in the blank" : "Rewrite the sentence";
    var gapPlaceholder = q.qtype === "gap" && offersBlankGap() ? "(leave blank if nothing goes here)" : "";
    root.innerHTML =
      '<div class="progress-bar"><div class="progress-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="q-meta"><span>Question ' + (state.idx + 1) + ' of ' + total + '</span><span>Score: ' + state.score + '</span></div>' +
      '<div class="q-card">' +
        '<div class="q-prompt">' + promptLabel + '</div>' +
        '<div class="q-text">' + q.prompt + '</div>' +
        (isTyped
          ? '<div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">' +
              '<input type="text" class="gram-gap-input" id="grammarQuizInput" autocomplete="off" spellcheck="false" placeholder="' + gapPlaceholder + '">' +
              '<button type="button" class="btn" id="grammarQuizCheckBtn">Check</button>' +
            '</div>'
          : '<div class="q-options">' +
              q.options.map(function(opt, i){
                return '<button type="button" class="q-opt" data-i="' + i + '">' + opt + '</button>';
              }).join("") +
            '</div>') +
        '<div class="q-feedback"></div>' +
        '<div class="q-next" style="display:none;"><button type="button" class="btn" id="grammarQuizNextBtn"></button></div>' +
      '</div>';
    if (isTyped){
      var input = document.getElementById("grammarQuizInput");
      document.getElementById("grammarQuizCheckBtn").addEventListener("click", function(){ checkTyped(q, input); });
      input.addEventListener("keydown", function(e){ if (e.key === "Enter") checkTyped(q, input); });
      input.focus();
    } else {
      root.querySelectorAll(".q-opt").forEach(function(btn){
        btn.addEventListener("click", function(){ checkMcq(q, btn); });
      });
    }
  }

  function showFeedback(isCorrect, feedbackHtml){
    if (isCorrect) state.score++;
    root.querySelector(".q-feedback").innerHTML = feedbackHtml;
    root.querySelector(".q-meta span:last-child").textContent = "Score: " + state.score;
    var nextWrap = root.querySelector(".q-next");
    var nextBtn = document.getElementById("grammarQuizNextBtn");
    var isLast = state.idx + 1 === state.questions.length;
    nextBtn.textContent = isLast ? "See Results" : "Next Question";
    nextWrap.style.display = "flex";
    nextBtn.addEventListener("click", function(){
      state.idx++;
      if (state.idx < state.questions.length) renderQuestion();
      else renderResults();
    });
  }

  function checkMcq(q, selectedBtn){
    var correctIdx = q.answers[0];
    var selectedIdx = Number(selectedBtn.dataset.i);
    var isCorrect = selectedIdx === correctIdx;
    root.querySelectorAll(".q-opt").forEach(function(btn){
      btn.disabled = true;
      if (Number(btn.dataset.i) === correctIdx) btn.classList.add("correct");
      else if (btn === selectedBtn) btn.classList.add("wrong");
    });
    var feedback = "<b>" + (isCorrect ? "Correct!" : "Not quite.") + "</b> " + q.why;
    showFeedback(isCorrect, feedback);
  }

  function checkTyped(q, input){
    if (input.disabled) return;
    var typed = grammarNorm(input.value);
    var acceptsBlank = blankMeansNoAnswer(q);
    var blankIsAnswerChoice = q.qtype === "gap" && offersBlankGap();
    if (!typed && !acceptsBlank && !blankIsAnswerChoice){
      root.querySelector(".q-feedback").innerHTML = "Type an answer first, or check the hint if the blank can be left empty.";
      return;
    }
    var expected = expectedAnswers(q);
    var isCorrect = typed ? expected.some(function(a){ return grammarNorm(a) === typed; }) : acceptsBlank;
    input.disabled = true;
    document.getElementById("grammarQuizCheckBtn").disabled = true;
    input.classList.add(isCorrect ? "correct" : "wrong");
    var feedback = isCorrect
      ? "<b>Correct!</b> " + q.why
      : "<b>Not quite.</b> The answer is \"" + expected[0] + "\". " + q.why;
    showFeedback(isCorrect, feedback);
  }

  function animateScore(el, target, total, duration){
    var start = null;
    function step(ts){
      if (start === null) start = ts;
      var progress = Math.min((ts - start) / duration, 1);
      el.textContent = Math.round(progress * target) + " / " + total;
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function renderResults(){
    var total = state.questions.length;
    var pct = total > 0 ? Math.round((state.score / total) * 100) : 0;
    if (state.mode === "topic" && root.dataset.authenticated === "1") syncMastery(pct);
    var masteredMsg = state.mode === "topic"
      ? (pct >= PASS_PCT ? "You've mastered this topic!" : "Score " + PASS_PCT + "%+ to master this topic.")
      : "";
    var secondaryAction = state.mode === "topic"
      ? '<a class="btn" href="/grammar/category/' + topicSlug + '/">Back to Lesson</a>'
      : '<a class="btn" href="/grammar/quiz/">Change Settings</a>';
    root.innerHTML =
      '<div class="result-card">' +
        '<h2>Quiz Complete</h2>' +
        '<div class="result-score" id="grammarQuizScoreNum">0 / ' + total + '</div>' +
        (masteredMsg ? '<p class="result-msg">' + masteredMsg + '</p>' : '') +
        '<div class="result-actions">' +
          '<button type="button" class="btn" id="grammarQuizRetryBtn">Try Again</button>' +
          secondaryAction +
          '<a class="btn" href="/grammar/">Back to Grammar</a>' +
        '</div>' +
      '</div>';
    animateScore(document.getElementById("grammarQuizScoreNum"), state.score, total, 700);
    document.getElementById("grammarQuizRetryBtn").addEventListener("click", function(){
      state.idx = 0;
      state.score = 0;
      state.questions = drawQuestions();
      renderQuestion();
    });
  }

  function initTopicMode(){
    fetch("/api/grammar/").then(function(r){ return r.json(); }).then(function(stages){
      var found = null;
      stages.forEach(function(stage){
        stage.topics.forEach(function(t){
          if (t.slug === topicSlug) found = t;
        });
      });
      if (!found || !found.quiz || !found.quiz.length){
        renderError("This topic doesn't have any quiz questions yet.");
        return;
      }
      state.topic = found;
      state.pool = found.quiz;
      state.drawCount = DRAW_COUNT;
      state.questions = drawQuestions();
      renderQuestion();
    }).catch(function(){
      renderError("Couldn't load quiz data — check your connection and try again.");
    });
  }

  function initTestMode(){
    var params = new URLSearchParams(window.location.search);
    var qtypeFilter = params.get("qtype") || "mixed";
    var countParam = params.get("count") || "10";
    var sectionFilter = params.get("section") || "";
    var cefrFilter = params.get("cefr") || "";
    var topicsFilter = params.get("topics") ? params.get("topics").split(",") : [];
    fetch("/api/grammar/").then(function(r){ return r.json(); }).then(function(stages){
      var pool = [];
      stages.forEach(function(stage){
        stage.topics.forEach(function(topic){
          if (sectionFilter && (!topic.section || topic.section.slug !== sectionFilter)) return;
          if (cefrFilter && topic.cefr !== cefrFilter) return;
          if (topicsFilter.length && topicsFilter.indexOf(topic.slug) === -1) return;
          topic.quiz.forEach(function(q){
            if (qtypeFilter !== "mixed" && q.qtype !== qtypeFilter) return;
            pool.push(q);
          });
        });
      });
      if (!pool.length){
        renderError("No questions match this combination — try different settings.");
        return;
      }
      state.pool = pool;
      state.drawCount = Math.min(parseInt(countParam, 10) || 10, GRAMTEST_MAX, pool.length);
      state.questions = drawQuestions();
      renderQuestion();
    }).catch(function(){
      renderError("Couldn't load quiz data — check your connection and try again.");
    });
  }

  function init(){
    if (testMode) initTestMode(); else initTopicMode();
  }

  init();
})();
