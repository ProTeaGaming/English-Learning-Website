(function(){
  const ALLAUTH_BASE = '/_allauth/browser/v1';
  const AUTH_BASE = '/auth';

  function getCsrf(){
    return document.cookie.split(';').map(c => c.trim())
      .find(c => c.startsWith('csrftoken='))?.split('=')[1] ?? '';
  }

  function authFetch(url, opts = {}){
    return fetch(url, {
      credentials: 'same-origin',
      headers: { 'X-CSRFToken': getCsrf(), 'Content-Type': 'application/json', ...(opts.headers ?? {}) },
      ...opts,
    });
  }

  const authState = { step: "email", email: "", resetKey: null };

  function resetAuthForm(){
    authState.step = "email";
    authState.email = "";
    document.getElementById("authEmail").value = "";
    document.getElementById("authEmail").disabled = false;
    document.getElementById("authPassword").value = "";
    document.getElementById("authPassword").type = "password";
    document.getElementById("authPwToggle").innerHTML = `<svg class="ico" aria-hidden="true"><use href="#i-eye"/></svg>`;
    document.getElementById("authRememberMe").checked = false;
    document.getElementById("authName").value = "";
    document.getElementById("authUsername").value = "";
    document.getElementById("authPicture").value = "";
    document.getElementById("authAvatarPreviewWrap").classList.add("auth-hidden");
    document.getElementById("authAvatarPreview").src = "";
    document.getElementById("authPasswordGroup").classList.add("auth-hidden");
    document.getElementById("authSignupExtra").classList.add("auth-hidden");
    document.getElementById("authMfaGroup").classList.add("auth-hidden");
    document.getElementById("authMfaCode").value = "";
    document.getElementById("authResetGroup").classList.add("auth-hidden");
    document.getElementById("authResetPassword").value = "";
    document.getElementById("authResetPassword2").value = "";
    document.getElementById("authForgotWrap").classList.add("auth-hidden");
    document.getElementById("authSwitch").classList.add("auth-hidden");
    document.getElementById("authRegisterHint").classList.remove("auth-hidden");
    document.getElementById("authEmailGroup").classList.remove("auth-hidden");
    document.getElementById("authSocialHint").classList.add("auth-hidden");
    document.getElementById("authError").textContent = "";
    showAuthInfo("");
    document.getElementById("authTitle").textContent = t("auth.signInTitle");
    document.getElementById("authSubmitBtn").textContent = t("auth.continue");
    document.getElementById("authSubmitBtn").disabled = false;
    document.getElementById("authSubmitBtn").classList.remove("auth-hidden");
  }

  function openAuthModal(){
    resetAuthForm();
    document.getElementById("authOverlay").classList.add("open");
    document.getElementById("authEmail").focus();
    document.body.style.overflow = "hidden";
  }

  function closeAuthModal(){
    document.getElementById("authOverlay").classList.remove("open");
    document.body.style.overflow = "";
  }

  function showAuthError(msg){
    document.getElementById("authError").textContent = msg;
  }

  function showAuthInfo(msg){
    const el = document.getElementById("authInfo");
    el.textContent = msg;
    el.classList.toggle("auth-hidden", !msg);
  }

  function showCheckEmailScreen(infoText){
    document.getElementById("authTitle").textContent = t("auth.checkEmailTitle");
    document.getElementById("authEmailGroup").classList.add("auth-hidden");
    document.getElementById("authPasswordGroup").classList.add("auth-hidden");
    document.getElementById("authSignupExtra").classList.add("auth-hidden");
    document.getElementById("authForgotWrap").classList.add("auth-hidden");
    document.getElementById("authSubmitBtn").classList.add("auth-hidden");
    document.getElementById("authRegisterHint").classList.add("auth-hidden");
    const socialHint = document.getElementById("authSocialHint");
    socialHint.textContent = t("auth.orSignInSocial");
    socialHint.classList.remove("auth-hidden");
    document.getElementById("authSwitch").classList.remove("auth-hidden");
    document.getElementById("authSwitch").innerHTML = `<a href="#" id="authBackLink">${t("auth.backToSignIn")}</a>`;
    showAuthInfo(infoText);
  }

  function previewAvatarFile(file, wrapId, imgId){
    const wrap = document.getElementById(wrapId);
    const img = document.getElementById(imgId);
    if (!file){ wrap.classList.add("auth-hidden"); img.src = ""; return; }
    const reader = new FileReader();
    reader.onload = () => { img.src = reader.result; wrap.classList.remove("auth-hidden"); };
    reader.readAsDataURL(file);
  }

  function socialLogin(provider, process){
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/_allauth/browser/v1/auth/provider/redirect';
    const fields = {
      provider: provider,
      callback_url: window.location.origin + '/',
      process: process || 'login',
      csrfmiddlewaretoken: getCsrf()
    };
    for (const [name, value] of Object.entries(fields)) {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = name;
      input.value = value;
      form.appendChild(input);
    }
    document.body.appendChild(form);
    form.submit();
  }

  // Trimmed down from production's initAuth(): VLPE is server-rendered, so
  // the nav's logged-in state already comes from {% if user.is_authenticated %}
  // on the next page load (see the login/mfa/signup success handlers below,
  // which reload the page instead of refreshing client-side state). The one
  // piece with no server-side equivalent is auto-opening the modal when a
  // session has a pending, not-yet-verified signup.
  async function initAuth(){
    try {
      const res = await fetch(`${ALLAUTH_BASE}/auth/session`, { credentials: 'same-origin' });
      const data = await res.json();
      const flows = data?.data?.flows || [];
      const pendingVerifyEmail = !(data?.data?.user) && flows.some(f => f.id === "verify_email" && f.is_pending);
      if (pendingVerifyEmail){
        openAuthModal();
        showCheckEmailScreen(t("auth.emailNotVerifiedInfo"));
      }
    } catch(e){}
  }

  // Handle allauth email links that land here:
  //   /verify-email/<key>/   → POST the key to the headless verify endpoint
  //   /reset-password/<key>/ → show a set-new-password form
  async function handleAuthDeepLinks(){
    const verifyMatch = window.location.pathname.match(/^\/verify-email\/([^/]+)\/?$/);
    const resetMatch  = window.location.pathname.match(/^\/reset-password\/([^/]+)\/?$/);

    if (verifyMatch){
      const key = decodeURIComponent(verifyMatch[1]);
      try {
        const res = await authFetch(`${ALLAUTH_BASE}/auth/email/verify`, {
          method: 'POST',
          body: JSON.stringify({ key }),
        });
        const data = await res.json().catch(() => ({}));
        // allauth.headless returns 401 (not 200) even on a SUCCESSFUL
        // verify, since confirming an email doesn't by itself establish an
        // authenticated session under mandatory verification — the account
        // still needs a separate login afterward. Verified against real
        // django-allauth 65.18.0 responses: a genuine failure always
        // carries a top-level `errors` array (e.g. invalid_or_expired_key);
        // a success never does, regardless of HTTP status.
        const ok = !data.errors;
        try {
          sessionStorage.setItem("vlpe_flash", ok
            ? t("auth.emailVerified")
            : t("auth.verifyLinkInvalid"));
        } catch(e){}
      } catch(e){
        try { sessionStorage.setItem("vlpe_flash", t("auth.verifyFailed")); } catch(_){}
      }
      window.location.href = "/";
      return;
    }

    if (resetMatch){
      authState.resetKey = decodeURIComponent(resetMatch[1]);
      openAuthModal();
      authState.step = "reset";
      document.getElementById("authTitle").textContent = t("auth.setNewPasswordTitle");
      document.getElementById("authEmail").closest("label").classList.add("auth-hidden");
      document.getElementById("authPasswordGroup").classList.add("auth-hidden");
      document.getElementById("authSignupExtra").classList.add("auth-hidden");
      document.getElementById("authRegisterHint").classList.add("auth-hidden");
      document.getElementById("authResetGroup").classList.remove("auth-hidden");
      document.getElementById("authSubmitBtn").textContent = t("auth.resetPasswordBtn");
      showAuthInfo(t("auth.chooseNewPasswordInfo"));
    }
  }

  // signInBtn only exists in nav.html for logged-out users (it's inside the
  // {% else %} branch alongside {% if user.is_authenticated %}); guard it so
  // logged-in page loads don't throw here and abort the rest of this IIFE
  // (which would otherwise skip every other binding below plus initAuth()
  // and handleAuthDeepLinks() at the bottom of the file).
  const signInBtn = document.getElementById("signInBtn");
  if (signInBtn) signInBtn.addEventListener("click", openAuthModal);
  document.getElementById("authClose").addEventListener("click", closeAuthModal);
  document.getElementById("authOverlay").addEventListener("click", (e) => {
    if (e.target.id === "authOverlay") closeAuthModal();
  });

  document.getElementById("authSwitch").addEventListener("click", (e) => {
    if (e.target.id === "authBackLink"){
      e.preventDefault();
      resetAuthForm();
      document.getElementById("authEmail").focus();
    }
  });

  document.getElementById("authRegisterHint").addEventListener("click", (e) => {
    if (e.target.id !== "authRegisterLink") return;
    e.preventDefault();
    authState.step = "signup";
    showAuthError("");
    showAuthInfo("");
    document.getElementById("authTitle").textContent = t("auth.createAccountTitle");
    document.getElementById("authPasswordGroup").classList.remove("auth-hidden");
    document.getElementById("authForgotWrap").classList.add("auth-hidden");
    document.getElementById("authSignupExtra").classList.remove("auth-hidden");
    document.getElementById("authRegisterHint").classList.add("auth-hidden");
    document.getElementById("authSwitch").classList.remove("auth-hidden");
    document.getElementById("authSwitch").innerHTML = `${t("auth.alreadyHaveAccount")} <a href="#" id="authBackLink">${t("auth.signInTitle")}</a>`;
    document.getElementById("authSubmitBtn").textContent = t("auth.createAccountBtn");
    document.getElementById("authEmail").focus();
  });

  document.getElementById("authForgotLink").addEventListener("click", (e) => {
    e.preventDefault();
    authState.step = "forgot";
    showAuthError("");
    document.getElementById("authTitle").textContent = t("auth.resetPasswordTitle");
    document.getElementById("authPasswordGroup").classList.add("auth-hidden");
    document.getElementById("authSwitch").classList.add("auth-hidden");
    showAuthInfo(t("auth.willEmailResetLink").replace("{email}", authState.email));
    document.getElementById("authSubmitBtn").textContent = t("auth.sendResetLink");
  });

  document.getElementById("authPwToggle").addEventListener("click", () => {
    const input = document.getElementById("authPassword");
    const toggle = document.getElementById("authPwToggle");
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    toggle.innerHTML = `<svg class="ico" aria-hidden="true"><use href="#${show ? "i-eye-off" : "i-eye"}"/></svg>`;
  });

  document.getElementById("authPicture").addEventListener("change", (e) => {
    previewAvatarFile(e.target.files[0], "authAvatarPreviewWrap", "authAvatarPreview");
  });

  document.querySelectorAll(".auth-social-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      showAuthError("");
      showAuthInfo(t("auth.openingProviderSignIn").replace("{provider}", btn.dataset.provider));
      socialLogin(btn.dataset.provider);
    });
  });

  document.getElementById("authForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    showAuthError("");
    const submitBtn = document.getElementById("authSubmitBtn");

    if (authState.step === "email"){
      const email = document.getElementById("authEmail").value.trim();
      if (!email) return;
      submitBtn.disabled = true;
      try {
        const res = await authFetch(`${AUTH_BASE}/check-email/`, {
          method: 'POST',
          body: JSON.stringify({ email }),
        });
        const data = await res.json();
        if (!res.ok){ showAuthError(data.error || t("auth.somethingWrong")); return; }

        authState.email = email;
        document.getElementById("authEmail").disabled = true;
        document.getElementById("authPasswordGroup").classList.remove("auth-hidden");
        document.getElementById("authSwitch").classList.remove("auth-hidden");
        document.getElementById("authSwitch").innerHTML = `${t("auth.notYou")} <a href="#" id="authBackLink">${t("auth.useDifferentEmail")}</a>`;
        document.getElementById("authRegisterHint").classList.add("auth-hidden");
        showAuthInfo("");

        if (data.exists){
          authState.step = "login";
          document.getElementById("authTitle").textContent = t("auth.signInTitle");
          document.getElementById("authSignupExtra").classList.add("auth-hidden");
          document.getElementById("authForgotWrap").classList.remove("auth-hidden");
          submitBtn.textContent = t("auth.signInTitle");
        } else {
          authState.step = "signup";
          document.getElementById("authTitle").textContent = t("auth.createAccountTitle");
          document.getElementById("authSignupExtra").classList.remove("auth-hidden");
          document.getElementById("authForgotWrap").classList.add("auth-hidden");
          submitBtn.textContent = t("auth.createAccountBtn");
        }
        document.getElementById("authPassword").focus();
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }

    if (authState.step === "login"){
      const password = document.getElementById("authPassword").value;
      submitBtn.disabled = true;
      try {
        const res = await authFetch(`${ALLAUTH_BASE}/auth/login`, {
          method: 'POST',
          body: JSON.stringify({ email: authState.email, password }),
        });
        const data = await res.json();
        // MFA-enabled account: allauth returns 401 with a pending
        // mfa_authenticate flow. Switch to the 2FA code step instead of erroring.
        const flows = data?.data?.flows || [];
        if (res.status === 401 && flows.some(f => f.id === "mfa_authenticate")){
          authState.step = "mfa";
          document.getElementById("authTitle").textContent = t("auth.twoFactorTitle");
          document.getElementById("authPasswordGroup").classList.add("auth-hidden");
          document.getElementById("authForgotWrap").classList.add("auth-hidden");
          document.getElementById("authMfaGroup").classList.remove("auth-hidden");
          showAuthInfo(t("auth.mfaInfo"));
          submitBtn.textContent = t("auth.verify");
          document.getElementById("authMfaCode").focus();
          return;
        }
        // The password was correct (allauth got as far as flagging a pending
        // verify_email flow, not just re-showing "login") but the account's
        // email isn't verified yet — show the real reason instead of falling
        // through to "incorrect credentials".
        if (res.status === 401 && flows.some(f => f.id === "verify_email")){
          showCheckEmailScreen(t("auth.emailNotVerifiedInfo"));
          return;
        }
        if (data.status !== 200){ showAuthError((data.errors?.[0]?.message) || t("auth.incorrectCredentials")); return; }
        closeAuthModal();
        window.location.reload();
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }

    if (authState.step === "mfa"){
      const code = document.getElementById("authMfaCode").value.trim();
      if (!code){ showAuthError(t("auth.enterMfaCode")); return; }
      submitBtn.disabled = true;
      try {
        const res = await authFetch(`${ALLAUTH_BASE}/auth/2fa/authenticate`, {
          method: 'POST',
          body: JSON.stringify({ code }),
        });
        const data = await res.json();
        if (data.status !== 200){ showAuthError(t("auth.invalidMfaCode")); return; }
        closeAuthModal();
        window.location.reload();
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }

    if (authState.step === "reset"){
      const pw1 = document.getElementById("authResetPassword").value;
      const pw2 = document.getElementById("authResetPassword2").value;
      if (!pw1 || pw1.length < 8){ showAuthError(t("auth.passwordTooShort")); return; }
      if (pw1 !== pw2){ showAuthError(t("auth.passwordMismatch")); return; }
      submitBtn.disabled = true;
      try {
        const res = await authFetch(`${ALLAUTH_BASE}/auth/password/reset`, {
          method: 'POST',
          body: JSON.stringify({ key: authState.resetKey, password: pw1 }),
        });
        const data = await res.json();
        // Same allauth.headless quirk as email verification above: a
        // successful password reset also returns 401 (no session gets
        // established), so the only reliable success signal is the
        // absence of a top-level `errors` array — verified against real
        // django-allauth 65.18.0 responses, not assumed from status code.
        if (data.errors){
          showAuthError(data.errors[0]?.message || t("auth.resetFailed"));
          return;
        }
        sessionStorage.setItem("vlpe_flash", t("auth.passwordResetSuccess"));
        window.location.href = "/";
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }

    if (authState.step === "forgot"){
      submitBtn.disabled = true;
      try {
        await authFetch(`${ALLAUTH_BASE}/auth/password/request`, {
          method: 'POST',
          body: JSON.stringify({ email: authState.email }),
        });
        authState.step = "forgot-sent";
        document.getElementById("authTitle").textContent = t("auth.checkEmailTitle");
        showAuthInfo(t("auth.resetSentInfo").replace("{email}", authState.email));
        submitBtn.classList.add("auth-hidden");
        document.getElementById("authSwitch").innerHTML = `<a href="#" id="authBackLink">${t("auth.backToSignIn")}</a>`;
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }

    if (authState.step === "forgot-sent"){
      return;
    }

    if (authState.step === "signup"){
      const email = document.getElementById("authEmail").value.trim();
      const password = document.getElementById("authPassword").value;
      const name = document.getElementById("authName").value.trim();
      const username = document.getElementById("authUsername").value.trim();
      const pictureInput = document.getElementById("authPicture");

      if (!email){
        showAuthError(t("auth.enterEmail"));
        return;
      }
      if (!/^[\p{L}\s]{1,60}$/u.test(name)){
        showAuthError(t("auth.nameLettersOnly"));
        return;
      }
      if (!/^[A-Za-z0-9]{3,20}$/.test(username)){
        showAuthError(t("auth.usernameFormat"));
        return;
      }

      authState.email = email;
      submitBtn.disabled = true;
      try {
        const res = await authFetch(`${ALLAUTH_BASE}/auth/signup`, {
          method: 'POST',
          body: JSON.stringify({ email, username, password }),
        });
        const data = await res.json();
        // Mandatory email verification: allauth returns 401 with a pending
        // verify_email flow. The account WAS created — don't treat it as an error.
        const flows = data?.data?.flows || [];
        if (res.status === 401 && flows.some(f => f.id === "verify_email")){
          showCheckEmailScreen(t("auth.accountCreatedInfo"));
          return;
        }
        if (data.status !== 200){ showAuthError((data.errors?.[0]?.message) || t("auth.createAccountFailed")); return; }
        // Allauth headless doesn't accept name/picture — save them now that the account exists
        if (name || pictureInput.files[0]) {
          const pf = new FormData();
          if (name) pf.append('name', name);
          if (pictureInput.files[0]) pf.append('picture', pictureInput.files[0]);
          await fetch(`${AUTH_BASE}/update-profile/`, {
            method: 'POST', credentials: 'same-origin',
            headers: { 'X-CSRFToken': getCsrf() }, body: pf,
          }).catch(() => {});
        }
        closeAuthModal();
        window.location.reload();
      } catch(err){
        showAuthError(t("auth.networkError"));
      } finally {
        submitBtn.disabled = false;
      }
      return;
    }
  });

  // Show any one-shot flash message stashed before a redirect (e.g. password reset).
  (function showPendingFlash(){
    let msg = null;
    try { msg = sessionStorage.getItem("vlpe_flash"); sessionStorage.removeItem("vlpe_flash"); } catch(e){}
    if (msg){ openAuthModal(); showAuthInfo(msg); }
  })();

  initAuth();
  handleAuthDeepLinks();

  window.vlpeAuth = { getCsrf, authFetch, socialLogin, previewAvatarFile, AUTH_BASE, ALLAUTH_BASE };
})();
