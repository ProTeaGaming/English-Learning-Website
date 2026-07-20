(function(){
  document.querySelectorAll("[data-nav-toggle]").forEach(function(link){
    link.addEventListener("click", function(e){
      var group = link.closest(".nav-group");
      if (group && group.classList.contains("active")){
        e.preventDefault();
        group.classList.toggle("open");
      }
    });
  });

  document.addEventListener("click", function(e){
    if (!e.target.closest(".nav-group")){
      document.querySelectorAll(".nav-group.open").forEach(function(g){
        g.classList.remove("open");
      });
    }
    if (!e.target.closest("#mobileNavChip")){
      var chip = document.getElementById("mobileNavChip");
      if (chip) chip.classList.remove("open");
    }
  });

  var mobileToggle = document.getElementById("mobileNavToggle");
  if (mobileToggle){
    mobileToggle.addEventListener("click", function(){
      document.getElementById("mobileNavChip").classList.toggle("open");
    });
  }
})();
