(function(){
  document.querySelectorAll(".section-block").forEach(function(block){
    var header = block.querySelector(".section-block-header");
    var body = block.querySelector(".section-block-body");
    header.addEventListener("click", function(){
      var opening = !block.classList.contains("open");
      block.classList.toggle("open", opening);
      body.style.maxHeight = opening ? body.scrollHeight + "px" : "0";
    });
  });
})();
