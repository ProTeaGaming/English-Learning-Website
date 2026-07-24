(function(){
  var CYCLE = [null, "little", "learned"];
  var LABELS = { null: "Not Learned", little: "Little Bit", learned: "Learned" };

  function getCsrfToken(){
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function readState(btn){
    var raw = btn.dataset.state;
    return raw === "none" ? null : raw;
  }

  function paint(btn, stateValue){
    btn.dataset.state = stateValue === null ? "none" : stateValue;
    btn.textContent = LABELS[stateValue === null ? "null" : stateValue];
  }

  // Cycles one word's state (none -> little -> learned -> none) and
  // syncs it to the server via GET-then-merge-then-POST against
  // /auth/sync/, never sending a partial map. Used by both the single
  // word_detail.html toggle and each per-card toggle on
  // category_word_list.html.
  function vocabToggleWord(btn){
    var wordId = btn.dataset.wordId;
    var prevState = readState(btn);
    var nextState = CYCLE[(CYCLE.indexOf(prevState) + 1) % CYCLE.length];
    paint(btn, nextState);

    return fetch("/auth/sync/", { credentials: "same-origin" })
      .then(function(res){
        if (!res.ok) throw new Error("sync GET failed");
        return res.json();
      })
      .then(function(data){
        var learnMap = data.learn_map || {};
        if (nextState === null) delete learnMap[wordId];
        else learnMap[wordId] = nextState;
        return fetch("/auth/sync/", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          body: JSON.stringify({ learn_map: learnMap }),
        });
      })
      .then(function(res){
        if (!res.ok) throw new Error("sync POST failed");
        // The word modal can show a second toggle for the same word
        // alongside a list card's own toggle; keep every instance of
        // this word's button in sync, not just the one clicked.
        document.querySelectorAll(
          '.card-toggle[data-word-id="' + wordId + '"], .learn-state-btn[data-word-id="' + wordId + '"]'
        ).forEach(function(el){
          if (el !== btn) paint(el, nextState);
        });
      })
      .catch(function(){
        paint(btn, prevState);
      });
  }

  // Sets or clears every word ID in wordIds at once: mode "learned" sets
  // each to "learned"; mode "reset" deletes each key entirely (matching
  // vocabToggleWord's own none-state convention — learn_map stays sparse,
  // never gets an explicit "none" value).
  function vocabBulkSetCategory(wordIds, mode){
    return fetch("/auth/sync/", { credentials: "same-origin" })
      .then(function(res){
        if (!res.ok) throw new Error("sync GET failed");
        return res.json();
      })
      .then(function(data){
        var learnMap = data.learn_map || {};
        wordIds.forEach(function(wordId){
          if (mode === "reset") delete learnMap[wordId];
          else learnMap[wordId] = "learned";
        });
        return fetch("/auth/sync/", {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
          },
          body: JSON.stringify({ learn_map: learnMap }),
        });
      });
  }

  window.vocabToggleWord = vocabToggleWord;
  window.vocabBulkSetCategory = vocabBulkSetCategory;

  var btn = document.querySelector(".learn-state-btn");
  if (btn){
    btn.addEventListener("click", function(){ vocabToggleWord(btn); });
  }
})();
