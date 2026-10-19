(() => {
  const root = document.documentElement;
  const languageButton = document.getElementById('language');
  const themeButton = document.getElementById('theme');
  const copyButton = document.getElementById('copy-code');
  const code = document.getElementById('setup-code');
  const status = document.getElementById('copy-status');
  const systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
  const storage = {
    get(key) { try { return localStorage.getItem(key); } catch { return null; } },
    set(key, value) { try { localStorage.setItem(key, value); } catch { /* Preferences remain usable without storage. */ } }
  };
  let language;
  function setLanguage(next) {
    language = next === 'en' ? 'en' : 'zh';
    root.lang = language === 'en' ? 'en' : 'zh-CN';
    languageButton.textContent = language === 'en' ? '中文' : 'English';
    languageButton.setAttribute('aria-label', language === 'en' ? '切换至中文' : 'Switch to English');
    document.title = language === 'en' ? 'Quantitative Finance and Systematic Research | Yuxiao Ma' : '量化金融与系统化研究 | Yuxiao Ma';
    document.querySelector('meta[name="description"]').content = language === 'en' ? 'A bilingual quantitative finance course: 45 chapters, six projects, a Capstone, complete textbooks, Loom workbooks, and shared Notebooks.' : '量化金融与系统化研究：45章、六个项目与Capstone，中英文教材、Loom练习册与共享Notebook。';
    document.querySelectorAll('[data-doc-zh]').forEach(a => { a.href = 'https://github.com/YuxiaoMa66/quant_course/blob/main/' + a.dataset[language === 'en' ? 'docEn' : 'docZh']; });
    code.textContent = code.textContent.replace(/editions\/(zh|en)\//g, 'editions/' + language + '/');
    status.textContent = '';
    storage.set('quant-course-language', language);
    updateThemeLabel();
  }
  function isDark() { return root.dataset.theme ? root.dataset.theme === 'dark' : systemTheme.matches; }
  function updateThemeLabel() {
    const dark = isDark();
    themeButton.textContent = language === 'en' ? (dark ? 'Light' : 'Dark') : (dark ? '浅色' : '深色');
    themeButton.setAttribute('aria-label', language === 'en' ? 'Switch to ' + (dark ? 'light' : 'dark') + ' theme' : '切换至' + (dark ? '浅色' : '深色') + '主题');
  }
  const savedTheme = storage.get('quant-course-theme');
  if (savedTheme === 'light' || savedTheme === 'dark') root.dataset.theme = savedTheme;
  const requestedLanguage = new URLSearchParams(location.search).get('lang');
  setLanguage(['zh', 'en'].includes(requestedLanguage) ? requestedLanguage : storage.get('quant-course-language') || 'zh');
  languageButton.hidden = false;
  themeButton.hidden = false;
  languageButton.addEventListener('click', () => {
    setLanguage(language === 'en' ? 'zh' : 'en');
    const url = new URL(location.href);
    url.searchParams.set('lang', language);
    history.replaceState(null, '', url);
  });
  themeButton.addEventListener('click', () => {
    root.dataset.theme = isDark() ? 'light' : 'dark';
    storage.set('quant-course-theme', root.dataset.theme);
    updateThemeLabel();
  });
  systemTheme.addEventListener('change', updateThemeLabel);
  if (navigator.clipboard && window.isSecureContext) {
    copyButton.hidden = false;
    copyButton.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(code.textContent);
        status.textContent = language === 'en' ? 'Commands copied.' : '命令已复制。';
      } catch {
        status.textContent = language === 'en' ? 'Copy unavailable. Select the commands above and copy them manually.' : '无法自动复制，请选中上方命令手动复制。';
      }
    });
  }
})();
