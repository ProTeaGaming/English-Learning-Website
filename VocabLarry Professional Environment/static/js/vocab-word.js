(function(){
  var btn = document.querySelector(".learn-state-btn");
  if (!btn) return;

  var CYCLE = [null, "little", "learned"];
  var LABELS = { null: "Not Learned", little: "Little Bit", learned: "Learned" };

  function readState(){
    var raw = btn.dataset.state;
    return raw === "none" ? null : raw;
  }

  function paint(stateValue){
    btn.dataset.state = stateValue === null ? "none" : stateValue;
    btn.textContent = LABELS[stateValue === null ? "null" : stateValue];
  }

  function getCsrfToken(){
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  btn.addEventListener("click", function(){
    var wordId = btn.dataset.wordId;
    var prevState = readState();
    var nextState = CYCLE[(CYCLE.indexOf(prevState) + 1) % CYCLE.length];
    paint(nextState);

    fetch("/auth/sync/", { credentials: "same-origin" })
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
      })
      .catch(function(){
        paint(prevState);
      });
  });
})();
