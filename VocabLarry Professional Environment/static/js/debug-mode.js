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

  DEBUG_FORMS.topic = [
    { name: "slug", label: "Slug", type: "text" },
    { name: "title", label: "Title", type: "text" },
    { name: "tag", label: "Tag (section)", type: "text" },
    { name: "cefr_label", label: "CEFR label (e.g. B1+)", type: "text" },
    { name: "blurb", label: "Blurb", type: "textarea" },
    { name: "stage", label: "Stage", type: "select", options: function(){
        return [{ value: "beginner", label: "Basic" },
                { value: "independent", label: "Intermediate" },
                { value: "expert", label: "Advanced" }];
      } },
    { name: "order", label: "Order", type: "number" },
  ];

  function topicInitialFromEl(el){
    return {
      slug: el.dataset.slug, title: el.dataset.title, tag: el.dataset.tag,
      cefr_label: el.dataset.cefrLabel, blurb: el.dataset.blurb,
      stage: el.dataset.stage, order: Number(el.dataset.order),
    };
  }

  function debugSaveTopic(existingId, initial){
    openDebugModal({
      title: existingId ? "Edit topic" : "Add grammar topic",
      fields: DEBUG_FORMS.topic,
      initial: initial || { order: 0 },
      onSave: function(payload){
        var p = existingId ? debugFetch("/api/grammar/topics/" + existingId + "/", "PATCH", payload)
                            : debugFetch("/api/grammar/topics/", "POST", payload);
        return p.then(function(){ window.location.reload(); });
      },
    });
  }

  function debugDeleteTopic(id, label){
    if (!debugConfirm('Delete topic "' + label + '"? Its lesson blocks and questions are deleted too. This cannot be undone.')) return;
    debugFetch("/api/grammar/topics/" + id + "/", "DELETE").then(function(){
      window.location.reload();
    }).catch(function(e){
      alert("Delete failed" + (e && e.error ? ": " + e.error : ""));
    });
  }

  document.addEventListener("DOMContentLoaded", function(){
    document.querySelectorAll("[data-dbg-topic]").forEach(function(ctl){
      ctl.addEventListener("click", function(e){ e.preventDefault(); e.stopPropagation(); });
      var editBtn = ctl.querySelector(".dbg-edit-topic");
      var delBtn = ctl.querySelector(".dbg-delete-topic");
      if (editBtn) editBtn.addEventListener("click", function(){
        debugSaveTopic(ctl.dataset.id, topicInitialFromEl(ctl));
      });
      if (delBtn) delBtn.addEventListener("click", function(){
        debugDeleteTopic(ctl.dataset.id, ctl.dataset.title);
      });
    });
    var addTopicBtn = document.querySelector("[data-dbg-add-topic]");
    if (addTopicBtn) addTopicBtn.addEventListener("click", function(){ debugSaveTopic(null, null); });
  });

  DEBUG_FORMS.block = [
    { name: "type", label: "Type", type: "select", options: function(){
        return ["intro", "rule", "table", "examples", "tip"].map(function(v){ return { value: v, label: v }; });
      } },
    { name: "title", label: "Title", type: "text" },
    { name: "body", label: "Body", type: "textarea" },
    { name: "data", label: 'Data (JSON — table: {"head":[],"rows":[]}; examples: {"items":[{"en":"","note":""}]})', type: "json", emptyValue: {} },
    { name: "order", label: "Order", type: "number" },
  ];

  function blockInitialFromEl(el){
    return {
      type: el.dataset.type, title: el.dataset.title, body: el.dataset.body,
      data: el.dataset.data ? JSON.parse(el.dataset.data) : {}, order: Number(el.dataset.order),
    };
  }

  function debugSaveBlock(topicId, existingId, initial){
    openDebugModal({
      title: existingId ? "Edit lesson block" : "Add lesson block",
      fields: DEBUG_FORMS.block,
      initial: initial || { data: {}, order: 0 },
      onSave: function(payload){
        var p = existingId ? debugFetch("/api/grammar/blocks/" + existingId + "/", "PATCH", payload)
                            : debugFetch("/api/grammar/blocks/", "POST", Object.assign({}, payload, { topic: topicId }));
        return p.then(function(){ window.location.reload(); });
      },
    });
  }

  function debugDeleteBlock(id){
    if (!debugConfirm("Delete this lesson block? This cannot be undone.")) return;
    debugFetch("/api/grammar/blocks/" + id + "/", "DELETE").then(function(){
      window.location.reload();
    }).catch(function(e){
      alert("Delete failed" + (e && e.error ? ": " + e.error : ""));
    });
  }

  document.addEventListener("DOMContentLoaded", function(){
    var topicIdEl = document.querySelector("[data-topic-id]");
    var topicId = topicIdEl ? topicIdEl.dataset.topicId : null;
    document.querySelectorAll("[data-dbg-block]").forEach(function(ctl){
      ctl.addEventListener("click", function(e){ e.stopPropagation(); });
      var editBtn = ctl.querySelector(".dbg-edit-block");
      var delBtn = ctl.querySelector(".dbg-delete-block");
      if (editBtn) editBtn.addEventListener("click", function(){
        debugSaveBlock(topicId, ctl.dataset.id, blockInitialFromEl(ctl));
      });
      if (delBtn) delBtn.addEventListener("click", function(){
        debugDeleteBlock(ctl.dataset.id);
      });
    });
    var addBlockBtn = document.querySelector("[data-dbg-add-block]");
    if (addBlockBtn) addBlockBtn.addEventListener("click", function(){ debugSaveBlock(topicId, null, null); });
  });

  window.debugFetch = debugFetch;
  window.debugConfirm = debugConfirm;
})();
