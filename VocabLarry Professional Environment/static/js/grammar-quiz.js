(function(){
  var root = document.getElementById("grammarQuizRoot");
  if (!root) return;

  var topicSlug = root.dataset.topicSlug;
  var DRAW_COUNT = 10;
  var PASS_PCT = 80;

  var state = {
    topic: null,
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
    return String(s).replace(/[’‘]/g, "'").trim();
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

  function drawQuestions(topic){
    return shuffle(topic.quiz).slice(0, DRAW_COUNT);
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
          body: JSON.stringify({ grammar_map: grammarMap }),
        });
      })
      .catch(function(){
        // Best-effort: the results screen is already rendered and fully
        // usable regardless of whether the sync round-trip succeeds.
      });
  }

  function renderError(message){
    root.innerHTML = '<p class="grammar-quiz-error">' + message +
      ' <a href="/grammar/topic/' + topicSlug + '/">Back to topic</a></p>';
  }

  function renderQuestion(){
    var q = state.questions[state.idx];
    var total = state.questions.length;
    var pct = Math.round(((state.idx + 1) / total) * 100);
    var isTyped = q.qtype !== "mcq";
    var promptLabel = q.qtype === "mcq" ? "Choose the correct option:"
      : q.qtype === "gap" ? "Fill in the blank:" : "Rewrite the sentence:";
    var gapPlaceholder = q.qtype === "gap" && offersBlankGap() ? "(leave blank if nothing goes here)" : "";
    root.innerHTML =
      '<a class="grammar-quiz-leave" href="/grammar/topic/' + topicSlug + '/">&larr; Leave</a>' +
      '<div class="grammar-quiz-progress"><div class="grammar-quiz-progress-fill" style="width:' + pct + '%"></div></div>' +
      '<div class="grammar-quiz-meta"><span>Question ' + (state.idx + 1) + ' of ' + total + '</span><span>Score: ' + state.score + '</span></div>' +
      '<div class="grammar-quiz-card">' +
        '<div class="grammar-quiz-prompt">' + promptLabel + '</div>' +
        '<div class="grammar-quiz-text">' + q.prompt + '</div>' +
        (isTyped
          ? '<div class="grammar-quiz-typed-row">' +
              '<input type="text" class="grammar-quiz-input" id="grammarQuizInput" autocomplete="off" spellcheck="false" placeholder="' + gapPlaceholder + '">' +
              '<button type="button" class="btn" id="grammarQuizCheckBtn">Check</button>' +
            '</div>'
          : '<div class="grammar-quiz-options">' +
              q.options.map(function(opt, i){
                return '<button type="button" class="grammar-quiz-opt" data-i="' + i + '">' + opt + '</button>';
              }).join("") +
            '</div>') +
        '<div class="grammar-quiz-feedback"></div>' +
        '<div class="grammar-quiz-next" style="display:none;"><button type="button" class="btn" id="grammarQuizNextBtn"></button></div>' +
      '</div>';
    if (isTyped){
      var input = document.getElementById("grammarQuizInput");
      document.getElementById("grammarQuizCheckBtn").addEventListener("click", function(){ checkTyped(q, input); });
      input.addEventListener("keydown", function(e){ if (e.key === "Enter") checkTyped(q, input); });
      input.focus();
    } else {
      root.querySelectorAll(".grammar-quiz-opt").forEach(function(btn){
        btn.addEventListener("click", function(){ checkMcq(q, btn); });
      });
    }
  }

  function showFeedback(isCorrect, feedbackHtml){
    if (isCorrect) state.score++;
    root.querySelector(".grammar-quiz-feedback").innerHTML = feedbackHtml;
    root.querySelector(".grammar-quiz-meta span:last-child").textContent = "Score: " + state.score;
    var nextWrap = root.querySelector(".grammar-quiz-next");
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
    root.querySelectorAll(".grammar-quiz-opt").forEach(function(btn){
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
      root.querySelector(".grammar-quiz-feedback").innerHTML = "Type an answer first, or check the hint if the blank can be left empty.";
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

  function renderResults(){
    var total = state.questions.length;
    var pct = total > 0 ? Math.round((state.score / total) * 100) : 0;
    if (root.dataset.authenticated === "1") syncMastery(pct);
    var masteredMsg = pct >= PASS_PCT
      ? "You've mastered this topic!"
      : "Score " + PASS_PCT + "%+ to master this topic.";
    root.innerHTML =
      '<div class="grammar-quiz-results">' +
        '<h2>Quiz Complete</h2>' +
        '<div class="grammar-quiz-score">' + state.score + ' / ' + total + '</div>' +
        '<p class="grammar-quiz-pct">' + pct + '%</p>' +
        '<p class="grammar-quiz-mastered-msg">' + masteredMsg + '</p>' +
        '<div class="grammar-quiz-result-actions">' +
          '<button type="button" class="btn" id="grammarQuizRetryBtn">Try Again</button>' +
          '<a class="btn" href="/grammar/topic/' + topicSlug + '/">Back to Lesson</a>' +
          '<a class="btn" href="/grammar/">Back to Grammar</a>' +
        '</div>' +
      '</div>';
    document.getElementById("grammarQuizRetryBtn").addEventListener("click", function(){
      state.idx = 0;
      state.score = 0;
      state.questions = drawQuestions(state.topic);
      renderQuestion();
    });
  }

  function init(){
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
      state.questions = drawQuestions(found);
      renderQuestion();
    }).catch(function(){
      renderError("Couldn't load quiz data — check your connection and try again.");
    });
  }

  init();
})();
