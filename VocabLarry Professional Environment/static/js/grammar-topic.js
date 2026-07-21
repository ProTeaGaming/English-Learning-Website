(function(){
  var reveals = document.querySelectorAll(".gram-reveal");
  if (reveals.length && "IntersectionObserver" in window){
    var io = new IntersectionObserver(function(entries){
      entries.forEach(function(entry){
        if (entry.isIntersecting){
          entry.target.classList.add("in-view");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: "0px 0px -40px" });
    reveals.forEach(function(el){ io.observe(el); });
  }

  var cards = Array.prototype.slice.call(document.querySelectorAll(".gram-stage"));
  if (cards.length > 1){
    var last = cards[cards.length - 1];
    var START_OFFSET = 100;
    var END_OFFSET = 120;
    var rafId = null;

    function update(){
      rafId = null;
      var lastTop = last.getBoundingClientRect().top;
      cards.forEach(function(card, i){
        if (i === cards.length - 1) return;
        var cardTop = card.getBoundingClientRect().top;
        var progress;
        if (cardTop > START_OFFSET){
          progress = 0;
        } else {
          var total = START_OFFSET - END_OFFSET;
          var traveled = START_OFFSET - Math.min(lastTop, START_OFFSET);
          progress = total > 0 ? Math.min(Math.max(traveled / total, 0), 1) : (lastTop <= END_OFFSET ? 1 : 0);
        }
        var scale = 1 - (1 - 0.93) * progress;
        var blur = 6 * progress;
        var saturate = 1 - (1 - 0.75) * progress;
        var opacity = 1 - (1 - 0.55) * progress;
        card.style.transform = "scale(" + scale + ")";
        card.style.filter = "blur(" + blur + "px) saturate(" + saturate + ")";
        card.style.opacity = String(opacity);
      });
    }

    function onScroll(){
      if (rafId === null) rafId = requestAnimationFrame(update);
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    update();
  }
})();
