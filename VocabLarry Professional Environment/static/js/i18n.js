(function(){
  var STRINGS = {
    en: {
      "nav.vocabulary": "Vocabulary",
      "nav.quiz": "Quiz",
      "nav.grammar": "Grammar",
      "nav.grammarTest": "Grammar Test",
      "nav.comingSoon": "Coming soon",
      "nav.signIn": "Sign In",
      "nav.signOut": "Sign Out",
      "nav.signUp": "Sign Up",
      "hero.subtitle": "Build vocabulary and grammar skills for IELTS, one focused session at a time.",
      "hero.start": "Start Learning",
      "hero.grammar": "Practice Grammar",
      "home.badge": "IELTS Preparation · Band 5–9",
      "home.title1": "Master every word,",
      "home.title2": "say it till it stays.",
      "home.yourProgress": "Your Progress",
      "home.wordsLearned": "Words learned",
      "home.categoriesStarted": "Categories started",
      "home.complete": "Complete",
    },
    vi: {
      "nav.vocabulary": "Từ vựng",
      "nav.quiz": "Trắc nghiệm",
      "nav.grammar": "Ngữ pháp",
      "nav.grammarTest": "Kiểm tra ngữ pháp",
      "nav.comingSoon": "Sắp ra mắt",
      "nav.signIn": "Đăng nhập",
      "nav.signOut": "Đăng xuất",
      "nav.signUp": "Đăng ký",
      "hero.subtitle": "Xây dựng vốn từ vựng và ngữ pháp cho IELTS, từng buổi học tập trung.",
      "hero.start": "Bắt đầu học",
      "hero.grammar": "Luyện ngữ pháp",
      "home.badge": "Luyện thi IELTS · Band 5–9",
      "home.title1": "Học từng từ,",
      "home.title2": "ghi nhớ mãi mãi.",
      "home.yourProgress": "Tiến độ của bạn",
      "home.wordsLearned": "Từ đã học",
      "home.categoriesStarted": "Danh mục đã bắt đầu",
      "home.complete": "Hoàn thành",
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
