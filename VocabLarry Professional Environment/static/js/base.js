(function(){
  var STORAGE_KEY = "vlpe_theme";
  var root = document.documentElement;

  function applyTheme(theme){
    if (theme === "dark" || theme === "light"){
      root.setAttribute("data-theme", theme);
    } else {
      root.removeAttribute("data-theme");
    }
  }

  var saved = null;
  try { saved = localStorage.getItem(STORAGE_KEY); } catch(e) {}
  applyTheme(saved);

  var toggle = document.querySelector("[data-theme-toggle]");
  if (toggle){
    toggle.addEventListener("click", function(){
      var current = root.getAttribute("data-theme") ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      var next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      try { localStorage.setItem(STORAGE_KEY, next); } catch(e) {}
    });
  }
})();
