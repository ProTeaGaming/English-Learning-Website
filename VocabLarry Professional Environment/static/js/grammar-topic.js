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
    var START_OFFSET = 100;
    var END_OFFSET = 120;

    // .gram-stage is position:sticky, so its live getBoundingClientRect().top
    // freezes once pinned - it can't be used as a continuous scroll signal.
    // Instead, capture each card's natural (pre-stick) document-flow position
    // once up front, then compute progress purely from window.scrollY against
    // those fixed reference points - matching how GSAP ScrollTrigger itself
    // resolves trigger positions once at refresh time, not every frame.
    var cardTops = [];
    function measure(){
      cardTops = cards.map(function(card){
        return card.getBoundingClientRect().top + window.scrollY;
      });
    }
    measure();

    var rafId = null;
    function update(){
      rafId = null;
      var scrollY = window.scrollY;
      var lastNaturalTop = cardTops[cardTops.length - 1];
      var endScrollY = lastNaturalTop - END_OFFSET;
      cards.forEach(function(card, i){
        if (i === cards.length - 1) return;
        var cardStartScrollY = cardTops[i] - START_OFFSET;
        var progress;
        if (endScrollY <= cardStartScrollY || scrollY <= cardStartScrollY){
          progress = 0;
        } else {
          progress = (scrollY - cardStartScrollY) / (endScrollY - cardStartScrollY);
          progress = Math.min(Math.max(progress, 0), 1);
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
    window.addEventListener("resize", function(){
      measure();
      update();
    });
    update();
  }
})();
