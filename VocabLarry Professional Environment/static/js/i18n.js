(function(){
  var STRINGS = {
    en: {
      "nav.vocabulary": "Vocabulary",
      "nav.home": "Home",
      "nav.category": "Category",
      "nav.word": "Word",
      "nav.quiz": "Quiz",
      "nav.grammar": "Grammar",
      "nav.reading": "Reading",
      "nav.writing": "Writing",
      "nav.listening": "Listening",
      "nav.speaking": "Speaking",
      "vocab.searchCategories": "Search categories…",
      "common.cefrLevel": "CEFR Level",
      "common.progress": "Progress",
      "common.all": "All",
      "common.completed": "Completed",
      "common.inProgress": "In Progress",
      "common.notStarted": "Not Started",
      "common.clearFilters": "Clear filters",
      "vocab.markAllCompleted": "✓ Mark All Completed",
      "vocab.resetAll": "↺ Reset All",
      "common.allSections": "← All Sections",
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
      "vocabHome.badge": "5,000 words · 250 categories",
      "vocabHome.title1": "Build your word bank,",
      "vocabHome.title2": "one category at a time.",
      "vocabHome.subtitle": "Browse by topic, look up any word, or test yourself with a quiz — pick where to start below.",
      "vocabHome.descCategory": "Browse every word, grouped by topic and CEFR level.",
      "vocabHome.descWord": "Look up any word across the full dictionary.",
      "vocabHome.descQuiz": "Test yourself with definitions, synonyms, and gap-fills.",
      "grammarHome.badge": "47 topics · 14,100 questions",
      "grammarHome.title1": "Master the rules,",
      "grammarHome.title2": "not just the words.",
      "grammarHome.subtitle": "Browse grammar topics, look up reference tables, or practice with a quiz — pick where to start below.",
      "grammarHome.descCategory": "Browse every topic, from tenses to conditionals.",
      "grammarHome.descWord": "Reference tables for irregular verbs, comparisons, and linkers.",
      "grammarHome.descQuiz": "Practice across every topic at once.",
    },
    vi: {
      "nav.vocabulary": "Từ vựng",
      "nav.home": "Trang chủ",
      "nav.category": "Danh mục",
      "nav.word": "Từ",
      "nav.quiz": "Trắc nghiệm",
      "nav.grammar": "Ngữ pháp",
      "nav.reading": "Đọc",
      "nav.writing": "Viết",
      "nav.listening": "Nghe",
      "nav.speaking": "Nói",
      "vocab.searchCategories": "Tìm kiếm danh mục…",
      "common.cefrLevel": "Trình độ CEFR",
      "common.progress": "Tiến độ",
      "common.all": "Tất cả",
      "common.completed": "Hoàn thành",
      "common.inProgress": "Đang học",
      "common.notStarted": "Chưa bắt đầu",
      "common.clearFilters": "Xóa bộ lọc",
      "vocab.markAllCompleted": "✓ Đánh dấu tất cả đã học",
      "vocab.resetAll": "↺ Đặt lại tất cả",
      "common.allSections": "← Tất cả danh mục",
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
      "vocabHome.badge": "5.000 từ · 250 danh mục",
      "vocabHome.title1": "Xây dựng vốn từ,",
      "vocabHome.title2": "từng danh mục một.",
      "vocabHome.subtitle": "Duyệt theo chủ đề, tra từ, hoặc tự kiểm tra bằng bài trắc nghiệm — chọn nơi bắt đầu bên dưới.",
      "vocabHome.descCategory": "Duyệt mọi từ, được nhóm theo chủ đề và trình độ CEFR.",
      "vocabHome.descWord": "Tra cứu bất kỳ từ nào trong toàn bộ từ điển.",
      "vocabHome.descQuiz": "Tự kiểm tra với định nghĩa, từ đồng nghĩa và điền khuyết.",
      "grammarHome.badge": "47 chủ đề · 14.100 câu hỏi",
      "grammarHome.title1": "Nắm vững quy tắc,",
      "grammarHome.title2": "không chỉ từ vựng.",
      "grammarHome.subtitle": "Duyệt các chủ đề ngữ pháp, tra bảng tham khảo, hoặc luyện tập bằng bài trắc nghiệm — chọn nơi bắt đầu bên dưới.",
      "grammarHome.descCategory": "Duyệt mọi chủ đề, từ thì động từ đến câu điều kiện.",
      "grammarHome.descWord": "Bảng tham khảo động từ bất quy tắc, so sánh và từ nối.",
      "grammarHome.descQuiz": "Luyện tập trên tất cả chủ đề cùng lúc.",
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
