(function(){
  var STRINGS = {
    en: {
      "nav.vocabulary": "Vocabulary",
      "nav.grammar": "Grammar",
      "nav.comingSoon": "Coming soon",
      "nav.signIn": "Sign In",
      "nav.signOut": "Sign Out",
      "nav.signUp": "Sign Up",
      "hero.title": "Master every word, say it till it stays.",
      "hero.subtitle": "Build vocabulary and grammar skills for IELTS, one focused session at a time.",
      "hero.start": "Start Learning",
      "hero.grammar": "Practice Grammar",
    },
    vi: {
      "nav.vocabulary": "Từ vựng",
      "nav.grammar": "Ngữ pháp",
      "nav.comingSoon": "Sắp ra mắt",
      "nav.signIn": "Đăng nhập",
      "nav.signOut": "Đăng xuất",
      "nav.signUp": "Đăng ký",
      "hero.title": "Học từng từ, ghi nhớ mãi mãi.",
      "hero.subtitle": "Xây dựng vốn từ vựng và ngữ pháp cho IELTS, từng buổi học tập trung.",
      "hero.start": "Bắt đầu học",
      "hero.grammar": "Luyện ngữ pháp",
    },
  };
  var STORAGE_KEY = "vlpe_lang";

  function applyLang(lang){
    var dict = STRINGS[lang] || STRINGS.en;
    document.querySelectorAll("[data-i18n]").forEach(function(el){
      var key = el.getAttribute("data-i18n");
      if (dict[key]) el.textContent = dict[key];
    });
    document.documentElement.setAttribute("lang", lang);
  }

  var saved = "en";
  try { saved = localStorage.getItem(STORAGE_KEY) || "en"; } catch(e) {}
  applyLang(saved);

  var toggle = document.querySelector("[data-lang-toggle]");
  if (toggle){
    toggle.addEventListener("click", function(){
      var current = document.documentElement.getAttribute("lang") || "en";
      var next = current === "en" ? "vi" : "en";
      applyLang(next);
      try { localStorage.setItem(STORAGE_KEY, next); } catch(e) {}
    });
  }
})();
