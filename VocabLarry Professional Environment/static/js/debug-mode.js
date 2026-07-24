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

  function openDebugModal(opts){
    var title = opts.title, fields = opts.fields, initial = opts.initial || {}, onSave = opts.onSave;
    var overlay = document.createElement("div");
    overlay.className = "dbg-overlay";
    function inputHtml(f){
      var val = initial[f.name];
      if (f.type === "select"){
        var opts2 = f.options().map(function(o){
          return '<option value="' + String(o.value).replace(/"/g, "&quot;") + '" ' +
            (String(val) === String(o.value) ? "selected" : "") + ">" +
            String(o.label).replace(/</g, "&lt;") + "</option>";
        }).join("");
        return '<select name="' + f.name + '">' + opts2 + "</select>";
      }
      if (f.type === "textarea" || f.type === "json"){
        var text = f.type === "json"
          ? (val === undefined ? "" : JSON.stringify(val))
          : (val == null ? "" : val);
        return '<textarea name="' + f.name + '" rows="3">' + String(text).replace(/</g, "&lt;") + "</textarea>";
      }
      var text2 = f.type === "csv" ? (val || []).join(", ") : (val == null ? "" : val);
      var type = f.type === "number" ? "number" : "text";
      return '<input type="' + type + '" name="' + f.name + '" value="' + String(text2).replace(/"/g, "&quot;") + '">';
    }
    overlay.innerHTML =
      '<div class="dbg-modal" role="dialog" aria-modal="true">' +
      "<h3>" + String(title).replace(/</g, "&lt;") + "</h3>" +
      "<form>" +
      fields.map(function(f){
        return '<label class="dbg-field" data-field="' + f.name + '">' +
          "<span>" + String(f.label).replace(/</g, "&lt;") + "</span>" +
          inputHtml(f) +
          '<em class="dbg-err" hidden></em></label>';
      }).join("") +
      '<div class="dbg-form-err" hidden></div>' +
      '<div class="dbg-actions">' +
      '<button type="button" class="dbg-cancel">Cancel</button>' +
      '<button type="submit" class="dbg-save">Save</button>' +
      "</div></form></div>";
    function close(){ overlay.remove(); document.removeEventListener("keydown", esc); }
    function esc(e){ if (e.key === "Escape") close(); }
    document.addEventListener("keydown", esc);
    overlay.addEventListener("click", function(e){ if (e.target === overlay) close(); });
    overlay.querySelector(".dbg-cancel").addEventListener("click", close);
    overlay.querySelector("form").addEventListener("submit", function(e){
      e.preventDefault();
      var payload = {};
      var parseError = false;
      fields.forEach(function(f){
        var el = overlay.querySelector('[name="' + f.name + '"]');
        var fieldBox = overlay.querySelector('.dbg-field[data-field="' + f.name + '"] .dbg-err');
        fieldBox.hidden = true;
        if (f.type === "csv"){
          payload[f.name] = el.value.split(",").map(function(s){ return s.trim(); }).filter(Boolean);
        } else if (f.type === "json"){
          try { payload[f.name] = el.value.trim() ? JSON.parse(el.value) : (f.emptyValue !== undefined ? f.emptyValue : {}); }
          catch (err) { fieldBox.textContent = "Invalid JSON."; fieldBox.hidden = false; parseError = true; }
        } else if (f.type === "number"){
          payload[f.name] = el.value === "" ? null : Number(el.value);
        } else {
          payload[f.name] = el.value;
        }
      });
      if (parseError) return;
      onSave(payload).then(close).catch(function(err){
        var errors = err && err.errors ? err.errors : { __all__: ["Save failed."] };
        Object.keys(errors).forEach(function(field){
          var box = overlay.querySelector('.dbg-field[data-field="' + field + '"] .dbg-err')
            || overlay.querySelector(".dbg-form-err");
          var msgs = errors[field];
          box.textContent = Array.isArray(msgs) ? msgs.join(" ") : String(msgs);
          box.hidden = false;
        });
      });
    });
    document.body.appendChild(overlay);
  }

  var DEBUG_FORMS = {
    word: [
      { name: "word", label: "Word", type: "text" },
      { name: "pos", label: "Part of speech", type: "text" },
      { name: "definition", label: "Definition", type: "textarea" },
      { name: "example", label: "Example", type: "textarea" },
      { name: "gap", label: "Gap sentence", type: "textarea" },
      { name: "synonyms", label: "Synonyms (comma-separated)", type: "csv" },
      { name: "antonyms", label: "Antonyms (comma-separated)", type: "csv" },
      { name: "category", label: "Category ID", type: "number" },
      { name: "cefr_level", label: "CEFR level ID", type: "number" },
      { name: "order", label: "Order", type: "number" },
    ],
  };

  function wordInitialFromEl(el){
    return {
      word: el.dataset.word, pos: el.dataset.pos, definition: el.dataset.definition,
      example: el.dataset.example, gap: el.dataset.gap,
      synonyms: el.dataset.synonyms ? el.dataset.synonyms.split(",") : [],
      antonyms: el.dataset.antonyms ? el.dataset.antonyms.split(",") : [],
      category: el.dataset.category, cefr_level: el.dataset.cefrLevel, order: Number(el.dataset.order),
    };
  }

  function debugSaveWord(existingId, initial){
    openDebugModal({
      title: existingId ? "Edit word" : "Add word",
      fields: DEBUG_FORMS.word,
      initial: initial || { synonyms: [], antonyms: [], order: 0 },
      onSave: function(payload){
        var p = existingId ? debugFetch("/api/words/" + existingId + "/", "PATCH", payload)
                            : debugFetch("/api/words/", "POST", payload);
        return p.then(function(){ window.location.reload(); });
      },
    });
  }

  function debugDeleteWord(id, label){
    if (!debugConfirm('Delete "' + label + '"? This cannot be undone.')) return;
    debugFetch("/api/words/" + id + "/", "DELETE").then(function(){
      window.location.reload();
    }).catch(function(e){
      alert("Delete failed" + (e && e.error ? ": " + e.error : ""));
    });
  }

  document.addEventListener("DOMContentLoaded", function(){
    document.querySelectorAll("[data-dbg-word]").forEach(function(ctl){
      ctl.addEventListener("click", function(e){ e.preventDefault(); e.stopPropagation(); });
      var editBtn = ctl.querySelector(".dbg-edit-word");
      var delBtn = ctl.querySelector(".dbg-delete-word");
      if (editBtn) editBtn.addEventListener("click", function(){
        debugSaveWord(ctl.dataset.id, wordInitialFromEl(ctl));
      });
      if (delBtn) delBtn.addEventListener("click", function(){
        debugDeleteWord(ctl.dataset.id, ctl.dataset.word);
      });
    });
    var addWordBtn = document.getElementById("dbgAddWordBtn");
    if (addWordBtn) addWordBtn.addEventListener("click", function(){ debugSaveWord(null, null); });
  });

  DEBUG_FORMS.category = [
    { name: "slug", label: "Slug", type: "text" },
    { name: "name", label: "Name", type: "text" },
    { name: "icon", label: "Icon (emoji)", type: "text" },
    { name: "cefr_level", label: "CEFR level ID", type: "number" },
    { name: "color", label: "Color ID", type: "number" },
    { name: "order", label: "Order", type: "number" },
  ];

  function categoryInitialFromEl(el){
    return {
      slug: el.dataset.slug, name: el.dataset.name, icon: el.dataset.icon,
      cefr_level: el.dataset.cefrLevel, color: el.dataset.color, order: Number(el.dataset.order),
    };
  }

  function debugSaveCategory(existingId, initial){
    openDebugModal({
      title: existingId ? "Edit category" : "Add category",
      fields: DEBUG_FORMS.category,
      initial: initial || { order: 0 },
      onSave: function(payload){
        var p = existingId ? debugFetch("/api/categories/" + existingId + "/", "PATCH", payload)
                            : debugFetch("/api/categories/", "POST", payload);
        return p.then(function(){ window.location.reload(); });
      },
    });
  }

  function debugDeleteCategory(id, label){
    if (!debugConfirm('Delete category "' + label + '"? This cannot be undone.')) return;
    debugFetch("/api/categories/" + id + "/", "DELETE").then(function(){
      window.location.reload();
    }).catch(function(e){
      alert("Delete failed" + (e && e.error ? ": " + e.error : ""));
    });
  }

  document.addEventListener("DOMContentLoaded", function(){
    document.querySelectorAll("[data-dbg-category]").forEach(function(ctl){
      ctl.addEventListener("click", function(e){ e.preventDefault(); e.stopPropagation(); });
      var editBtn = ctl.querySelector(".dbg-edit-category");
      var delBtn = ctl.querySelector(".dbg-delete-category");
      if (editBtn) editBtn.addEventListener("click", function(){
        debugSaveCategory(ctl.dataset.id, categoryInitialFromEl(ctl));
      });
      if (delBtn) delBtn.addEventListener("click", function(){
        debugDeleteCategory(ctl.dataset.id, ctl.dataset.name);
      });
    });
    var addCategoryBtn = document.querySelector("[data-dbg-add-category]");
    if (addCategoryBtn) addCategoryBtn.addEventListener("click", function(){ debugSaveCategory(null, null); });
  });

  window.debugFetch = debugFetch;
  window.debugConfirm = debugConfirm;
})();
