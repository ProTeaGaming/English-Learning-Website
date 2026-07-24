(function(){
  var modalOpen = false;

  function bindLearnStateBtn(container){
    var btn = container.querySelector(".learn-state-btn");
    if (btn) btn.addEventListener("click", function(){ window.vocabToggleWord(btn); });
  }

  function showModal(){
    document.getElementById("wordModalOverlay").classList.add("open");
    document.body.style.overflow = "hidden";
    modalOpen = true;
  }

  function hideModal(){
    document.getElementById("wordModalOverlay").classList.remove("open");
    document.body.style.overflow = "";
    modalOpen = false;
  }

  function loadWordInto(href){
    return fetch(href, {
      credentials: "same-origin",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    }).then(function(res){
      if (!res.ok) throw new Error("word fetch failed");
      return res.text();
    }).then(function(html){
      var content = document.getElementById("wordModalContent");
      content.innerHTML = html;
      bindLearnStateBtn(content);
      showModal();
    });
  }

  function openWordModal(href){
    return loadWordInto(href).then(function(){
      history.pushState({ wordModal: true }, "", href);
    });
  }

  document.addEventListener("click", function(e){
    var trigger = e.target.closest("[data-word-modal-trigger], .word-xref");
    if (!trigger) return;
    e.preventDefault();
    openWordModal(trigger.getAttribute("href"));
  });

  document.getElementById("wordModalClose").addEventListener("click", function(){
    history.back();
  });
  document.getElementById("wordModalOverlay").addEventListener("click", function(e){
    if (e.target.id === "wordModalOverlay") history.back();
  });

  window.addEventListener("popstate", function(e){
    if (e.state && e.state.wordModal){
      loadWordInto(location.pathname + location.search);
    } else if (modalOpen){
      hideModal();
    }
  });

  window.openWordModal = openWordModal;
})();
