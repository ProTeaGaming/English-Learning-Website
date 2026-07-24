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
    if (trigger){
      e.preventDefault();
      openWordModal(trigger.getAttribute("href"));
      return;
    }
    // The hover-reveal panel on word-card list items (category_word_list.html,
    // word_list.html) sits on top of the title link once :hover shows it
    // (.reveal is position:absolute with pointer-events:auto while visible,
    // same footprint as .face) — a real mouse click can never reach the
    // underlying <a> once hovered. Delegate at the whole-card level instead,
    // matching production's own card.addEventListener("click", ...) pattern:
    // any click inside .word-card resolves to that card's own trigger link,
    // except on the progress-toggle button itself — .card-toggle is the
    // class these two card templates actually use (word_detail_card.html's
    // own toggle, elsewhere, uses .learn-state-btn instead; excluding both
    // covers every context this listener runs in).
    if (e.target.closest(".learn-state-btn, .card-toggle")) return;
    var card = e.target.closest(".word-card");
    if (!card) return;
    var cardTrigger = card.querySelector("[data-word-modal-trigger]");
    if (!cardTrigger) return;
    e.preventDefault();
    openWordModal(cardTrigger.getAttribute("href"));
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
