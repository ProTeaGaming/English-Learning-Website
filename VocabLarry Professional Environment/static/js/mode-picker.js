(function(){
  function openModePicker(intent){
    var titleKey = intent === "test" ? "home.chooseTest" : "home.chooseLearn";
    document.getElementById("modePickerTitle").textContent = window.t(titleKey);

    var vocabRow = document.getElementById("modePickerVocab");
    var grammarRow = document.getElementById("modePickerGrammar");
    vocabRow.onclick = function(){
      window.location.href = intent === "test" ? vocabRow.dataset.testHref : vocabRow.dataset.learnHref;
    };
    grammarRow.onclick = function(){
      window.location.href = intent === "test" ? grammarRow.dataset.testHref : grammarRow.dataset.learnHref;
    };

    document.getElementById("modePickerOverlay").classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeModePicker(){
    document.getElementById("modePickerOverlay").classList.remove("open");
    document.body.style.overflow = "";
  }

  document.getElementById("modePickerClose").addEventListener("click", closeModePicker);
  document.getElementById("modePickerOverlay").addEventListener("click", function(e){
    if (e.target.id === "modePickerOverlay") closeModePicker();
  });

  window.openModePicker = openModePicker;
  window.closeModePicker = closeModePicker;
})();
