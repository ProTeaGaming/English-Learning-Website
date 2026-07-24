(function(){
  function getCsrfToken(){
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function debugFetch(url, method, payload){
    return fetch(url, {
      method: method,
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
      body: payload === undefined ? undefined : JSON.stringify(payload),
    }).then(function(res){
      return res.json().catch(function(){ return {}; }).then(function(data){
        if (!res.ok) throw data;
        return data;
      });
    });
  }

  function debugConfirm(message){
    return window.confirm(message);
  }

  function debugOn(){
    return sessionStorage.getItem("debugMode") === "1";
  }

  function updateToggleLabel(){
    var btn = document.getElementById("debugToggle");
    if (btn) btn.textContent = "Debug mode: " + (debugOn() ? "On" : "Off");
  }

  function applyDebugMode(){
    document.body.classList.toggle("debug-on", debugOn());
    var ribbon = document.getElementById("debugRibbon");
    if (debugOn() && !ribbon){
      ribbon = document.createElement("div");
      ribbon.id = "debugRibbon";
      ribbon.textContent = "DEBUG";
      document.body.appendChild(ribbon);
    } else if (!debugOn() && ribbon){
      ribbon.remove();
    }
  }

  document.addEventListener("DOMContentLoaded", function(){
    applyDebugMode();
    updateToggleLabel();
    var toggleBtn = document.getElementById("debugToggle");
    if (toggleBtn){
      toggleBtn.addEventListener("click", function(){
        sessionStorage.setItem("debugMode", debugOn() ? "0" : "1");
        updateToggleLabel();
        applyDebugMode();
      });
    }
  });

  window.debugFetch = debugFetch;
  window.debugConfirm = debugConfirm;
})();
