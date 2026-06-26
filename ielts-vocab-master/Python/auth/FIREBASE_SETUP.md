# Setting up social login (Google / Facebook / Apple / Microsoft)

Social sign-in goes through Firebase Authentication. Firebase handles the
OAuth popup/redirect dance and hands the frontend a verified ID token;
`auth/firebase_login.php` verifies that token and creates/links a row in
the existing `users` table. Email/password sign-in is untouched by any of
this.

Firebase does **not** remove the need to register an app with each
vendor — it's where you paste those vendors' credentials in.

## 1. Create the Firebase project

1. Go to the [Firebase console](https://console.firebase.google.com/),
   create a project (the free Spark plan is enough for this).
2. Project settings (gear icon) → General → "Your apps" → add a **Web
   app**. Firebase shows you a `firebaseConfig` object with `apiKey`,
   `authDomain`, `projectId`, etc.
3. Copy that into `vocab-master.html`'s `firebaseConfig` (near the bottom
   of the file, in the `<script type="module">` block) — these values
   are public/client-safe, not secrets.
4. Copy just the `apiKey` value into `auth/config.local.php` under
   `firebase.api_key` (copy `auth/config.local.example.php` to
   `auth/config.local.php` first if you haven't already, for the mail
   settings).

## 2. Enable each provider

In the Firebase console: **Authentication → Sign-in method → Add new
provider.**

- **Google** — toggle it on, pick a support email. No external app
  registration needed; Firebase handles Google entirely itself.
- **Facebook** — needs a [Meta for Developers](https://developers.facebook.com/)
  app first: create an app → add the "Facebook Login" product → copy
  its App ID and App Secret into Firebase's Facebook provider screen.
  Firebase shows you an OAuth redirect URI to paste into the Facebook
  app's Valid OAuth Redirect URIs.
- **Apple** — needs an **Apple Developer Program membership ($99/yr)**:
  1. Apple Developer → Certificates, IDs & Profiles → Identifiers → new
     **Services ID** (this is the OAuth client ID), enable "Sign in with
     Apple" on it, and configure it with the domain + redirect URI
     Firebase's Apple provider screen gives you.
  2. Apple Developer → Keys → new key with "Sign in with Apple" enabled,
     download the `.p8` file (one-time download — save it).
  3. Back in Firebase's Apple provider screen: enter the Services ID,
     Apple Team ID, Key ID, and paste the contents of the `.p8` file.
  4. Apple's redirect URI must be HTTPS — `localhost` is not accepted by
     Apple, but `signInWithPopup` from the browser works fine for local
     dev since the popup itself is served from Apple's domain; Firebase
     is the HTTPS endpoint Apple redirects to, not your local PHP server.
- **Microsoft** — needs an [Azure AD app registration](https://portal.azure.com/)
  (App registrations → New registration) → copy its Application
  (client) ID and a generated client secret into Firebase's Microsoft
  provider screen, and add the redirect URI Firebase gives you to the
  Azure app's Authentication settings.

## 3. Authorized domains

Authentication → Settings → Authorized domains. `localhost` is included
by default, so `php -S localhost:8000` works without extra config. Add
your real domain here once one exists.

## 4. Try it

Until `firebaseConfig.apiKey` in `vocab-master.html` is changed from the
`YOUR_FIREBASE_WEB_API_KEY` placeholder, the 4 social buttons (and the
"or" divider above the email field) are hidden from the sign-in modal
entirely — visitors just see the plain email/password form, no broken
buttons or raw Firebase errors.

Once you fill in a real `firebaseConfig` and enable at least one
provider, reload the page — the social row reappears automatically.
Click a button to open Firebase's popup; on success it calls
`auth/firebase_login.php`, which creates or matches a `users` row and
logs you in. If a provider isn't enabled yet in the Firebase console,
that specific button will still show a Firebase error in the modal
(e.g. `auth/operation-not-allowed`) rather than being hidden — only the
fully-unconfigured (placeholder API key) case hides everything.
