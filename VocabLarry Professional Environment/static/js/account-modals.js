(function(){
  const { getCsrf, authFetch, socialLogin, previewAvatarFile, AUTH_BASE, ALLAUTH_BASE } = window.vlpeAuth;

  function t(key){ return window.t ? window.t(key) : key; }

  /* ── User-chip open/close (mirrors the .nav-group/.lang-chip pattern
     already established in nav.js/i18n.js) ─────────────────────────── */
  const userChip = document.querySelector('[data-user-chip]');
  if (userChip){
    userChip.addEventListener('click', function(e){
      e.stopPropagation();
      userChip.classList.toggle('open');
    });
    document.addEventListener('click', function(e){
      if (!e.target.closest('[data-user-chip]')) userChip.classList.remove('open');
    });
  }

  /* ── Edit Profile modal ───────────────────────────────────────────── */
  const PROVIDER_LABELS = { google: 'Google', facebook: 'Facebook', microsoft: 'Microsoft', apple: 'Apple' };
  const PROVIDER_ICONS = {
    google: '<svg viewBox="0 0 24 24" width="22" height="22"><path fill="#4285F4" d="M23.49 12.27c0-.82-.07-1.42-.22-2.04H12v3.91h6.4c-.13 1.06-.83 2.66-2.39 3.74l-.02.14 3.47 2.69.24.02c2.21-2.04 3.79-5.04 3.79-8.46Z"/><path fill="#34A853" d="M12 24c3.24 0 5.95-1.07 7.93-2.91l-3.78-2.93c-1.02.71-2.38 1.21-4.15 1.21-3.16 0-5.84-2.07-6.79-4.96l-.14.01-3.6 2.78-.05.13C3.4 21.3 7.36 24 12 24Z"/><path fill="#FBBC05" d="M5.21 14.41A7.4 7.4 0 0 1 4.8 12c0-.84.15-1.65.4-2.41l-.01-.16-3.65-2.83-.12.06A11.97 11.97 0 0 0 0 12c0 1.93.47 3.76 1.42 5.34l3.79-2.93Z"/><path fill="#EA4335" d="M12 4.75c2.26 0 3.78.97 4.65 1.79l3.39-3.31C17.94 1.19 15.24 0 12 0 7.36 0 3.4 2.7 1.42 6.66l3.78 2.93C6.16 6.7 8.84 4.75 12 4.75Z"/></svg>',
    facebook: '<svg viewBox="0 0 24 24" width="22" height="22"><path fill="#1877F2" d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>',
    microsoft: '<svg viewBox="0 0 24 24" width="22" height="22"><path fill="#F25022" d="M1 1h10.3v10.3H1z"/><path fill="#7FBA00" d="M12.7 1H23v10.3H12.7z"/><path fill="#00A4EF" d="M1 12.7h10.3V23H1z"/><path fill="#FFB900" d="M12.7 12.7H23V23H12.7z"/></svg>',
    apple: '<svg viewBox="0 0 24 24" width="22" height="22"><path fill="currentColor" d="M16.365 1.43c0 1.14-.415 2.05-1.245 2.735-.83.685-1.83 1.08-2.996 1.18-.03-.06-.06-.19-.06-.4 0-1.1.42-2.05 1.26-2.85.42-.4.9-.71 1.44-.94.54-.23 1.05-.36 1.53-.4.02.2.03.4.03.6zm3.75 5.85c-.06.05-1.845 1.08-1.845 3.3 0 2.565 2.25 3.475 2.31 3.5-.01.06-.36 1.235-1.19 2.44-.74 1.06-1.51 2.115-2.72 2.135-1.19.02-1.57-.705-2.93-.705-1.365 0-1.79.685-2.915.725-1.17.04-2.06-1.15-2.81-2.205-1.53-2.16-2.7-6.1-1.13-8.755.78-1.32 2.175-2.155 3.69-2.175 1.15-.02 2.23.775 2.93.775.695 0 1.995-.955 3.365-.815.575.025 2.19.235 3.245 1.78z"/></svg>',
  };

  async function renderProfileConnections(){
    const list = document.getElementById('profileConnectionsList');
    const errEl = document.getElementById('profileConnectionsError');
    errEl.textContent = '';
    list.innerHTML = '<p class="sub">' + t('common.loading') + '</p>';
    let connected = [];
    try {
      const res = await authFetch(ALLAUTH_BASE + '/account/providers', { method: 'GET' });
      const data = await res.json();
      connected = (data.data || []).map(function(a){ return { provider: a.provider.id, uid: a.uid }; });
    } catch(e){
      list.innerHTML = '';
      errEl.textContent = t('auth.networkError');
      return;
    }
    list.innerHTML = Object.keys(PROVIDER_LABELS).map(function(provider){
      const acct = connected.find(function(a){ return a.provider === provider; });
      const btn = acct
        ? '<button type="button" class="profile-conn-btn profile-conn-disconnect" data-provider="' + provider + '" data-uid="' + acct.uid + '" data-action="disconnect">' + t('auth.disconnect') + '</button>'
        : '<button type="button" class="profile-conn-btn" data-provider="' + provider + '" data-action="connect">' + t('auth.connect') + '</button>';
      return '<div class="profile-conn-row">'
        + '<span class="profile-conn-icon">' + PROVIDER_ICONS[provider] + '</span>'
        + '<span class="profile-conn-name">' + PROVIDER_LABELS[provider] + '</span>'
        + (acct ? '<span class="profile-conn-status">' + t('auth.connected') + '</span>' : '')
        + btn + '</div>';
    }).join('');
    list.querySelectorAll("[data-action='connect']").forEach(function(btn){
      btn.addEventListener('click', function(){ socialLogin(btn.dataset.provider, 'connect'); });
    });
    list.querySelectorAll("[data-action='disconnect']").forEach(function(btn){
      btn.addEventListener('click', function(){ disconnectProvider(btn.dataset.provider, btn.dataset.uid); });
    });
  }

  async function disconnectProvider(provider, uid){
    const errEl = document.getElementById('profileConnectionsError');
    errEl.textContent = '';
    try {
      const res = await authFetch(ALLAUTH_BASE + '/account/providers', {
        method: 'DELETE',
        body: JSON.stringify({ provider: provider, account: uid }),
      });
      const data = await res.json();
      if (!res.ok){
        errEl.textContent = (data.errors && data.errors[0] && data.errors[0].message) || t('auth.disconnectFailed');
        return;
      }
      await renderProfileConnections();
    } catch(e){
      errEl.textContent = t('auth.networkError');
    }
  }

  const editProfileBtn = document.querySelector('[data-open-edit-profile]');
  const profileOverlay = document.getElementById('profileOverlay');
  if (editProfileBtn && profileOverlay){
    editProfileBtn.addEventListener('click', function(){
      if (userChip) userChip.classList.remove('open');
      document.getElementById('profileError').textContent = '';
      profileOverlay.classList.add('open');
      renderProfileConnections();
    });
    document.getElementById('profileClose').addEventListener('click', function(){
      profileOverlay.classList.remove('open');
    });
    profileOverlay.addEventListener('click', function(e){
      if (e.target.id === 'profileOverlay') profileOverlay.classList.remove('open');
    });
    document.getElementById('profilePicture').addEventListener('change', function(e){
      previewAvatarFile(e.target.files[0], 'profileAvatarPreviewWrap', 'profileAvatarPreview');
    });
    document.getElementById('profileForm').addEventListener('submit', async function(e){
      e.preventDefault();
      const errorEl = document.getElementById('profileError');
      errorEl.textContent = '';
      const name = document.getElementById('profileName').value.trim();
      const username = document.getElementById('profileUsername').value.trim();

      if (name && !/^[\p{L}\s]{1,60}$/u.test(name)){
        errorEl.textContent = t('auth.nameLettersOnly');
        return;
      }
      if (username && !/^[A-Za-z0-9]{3,20}$/.test(username)){
        errorEl.textContent = t('auth.usernameFormat');
        return;
      }

      const submitBtn = document.getElementById('profileSubmitBtn');
      submitBtn.disabled = true;
      try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('username', username);
        const pictureInput = document.getElementById('profilePicture');
        if (pictureInput.files[0]) formData.append('picture', pictureInput.files[0]);

        const res = await fetch(AUTH_BASE + '/update-profile/', {
          method: 'POST', credentials: 'same-origin',
          headers: { 'X-CSRFToken': getCsrf() }, body: formData,
        });
        const data = await res.json();
        if (!res.ok){ errorEl.textContent = data.error || t('auth.updateProfileFailed'); return; }
        profileOverlay.classList.remove('open');
        window.location.reload();
      } catch(err){
        errorEl.textContent = t('auth.networkError');
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  /* ── Delete Account modal ─────────────────────────────────────────── */
  const deleteAccountBtn = document.querySelector('[data-open-delete-account]');
  const deleteOverlay = document.getElementById('deleteOverlay');
  if (deleteAccountBtn && deleteOverlay){
    deleteAccountBtn.addEventListener('click', async function(){
      if (userChip) userChip.classList.remove('open');
      document.getElementById('deletePassword').value = '';
      document.getElementById('deleteError').textContent = '';
      let needsPassword = true;
      try {
        const res = await fetch(AUTH_BASE + '/session/', { credentials: 'same-origin' });
        const data = await res.json();
        needsPassword = data.hasPassword !== false;
      } catch(e){ /* default to requiring a password if the check fails */ }
      document.getElementById('deletePasswordGroup').style.display = needsPassword ? '' : 'none';
      document.getElementById('deletePassword').required = needsPassword;
      document.getElementById('deleteWarning').textContent = needsPassword
        ? t('auth.deleteAccountWarning')
        : t('auth.deleteAccountWarningNoPassword');
      deleteOverlay.classList.add('open');
    });
    document.getElementById('deleteClose').addEventListener('click', function(){
      deleteOverlay.classList.remove('open');
    });
    deleteOverlay.addEventListener('click', function(e){
      if (e.target.id === 'deleteOverlay') deleteOverlay.classList.remove('open');
    });
    document.getElementById('deleteForm').addEventListener('submit', async function(e){
      e.preventDefault();
      const password = document.getElementById('deletePassword').value;
      const submitBtn = document.getElementById('deleteSubmitBtn');
      const errorEl = document.getElementById('deleteError');
      errorEl.textContent = '';
      submitBtn.disabled = true;
      try {
        const res = await authFetch(AUTH_BASE + '/delete-account/', {
          method: 'POST',
          body: JSON.stringify({ password: password }),
        });
        const data = await res.json();
        if (!res.ok){ errorEl.textContent = data.error || t('auth.deleteAccountFailed'); return; }
        window.location.href = '/';
      } catch(err){
        errorEl.textContent = t('auth.networkError');
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  /* ── Reset Progress confirm overlay ───────────────────────────────── */
  const resetProgressBtn = document.querySelector('[data-open-reset-progress]');
  const resetOverlay = document.getElementById('resetOverlay');
  if (resetProgressBtn && resetOverlay){
    resetProgressBtn.addEventListener('click', function(){
      if (userChip) userChip.classList.remove('open');
      document.getElementById('resetError').textContent = '';
      resetOverlay.classList.add('open');
    });
    document.getElementById('resetClose').addEventListener('click', function(){
      resetOverlay.classList.remove('open');
    });
    document.getElementById('resetCancelBtn').addEventListener('click', function(){
      resetOverlay.classList.remove('open');
    });
    resetOverlay.addEventListener('click', function(e){
      if (e.target.id === 'resetOverlay') resetOverlay.classList.remove('open');
    });
    document.getElementById('resetConfirmBtn').addEventListener('click', async function(){
      const btn = document.getElementById('resetConfirmBtn');
      const errorEl = document.getElementById('resetError');
      errorEl.textContent = '';
      btn.disabled = true;
      try {
        const res = await authFetch(AUTH_BASE + '/reset-progress/', { method: 'POST' });
        if (!res.ok){ errorEl.textContent = t('auth.networkError'); return; }
        window.location.reload();
      } catch(err){
        errorEl.textContent = t('auth.networkError');
      } finally {
        btn.disabled = false;
      }
    });
  }
})();
