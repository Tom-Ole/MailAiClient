<script lang="ts">
  import { goto } from '$app/navigation';

  let email = $state('');
  let password = $state('');
  let imapHost = $state('');
  let smtpHost = $state('');
  let showAdvanced = $state(false);
  let loading = $state(false);
  let error = $state('');

  // Attempt to infer hosts from email domain
  function inferHosts() {
    const domain = email.split('@')[1];
    if (!domain) return;

    const known: Record<string, { imap: string; smtp: string }> = {
      'gmail.com':    { imap: 'imap.gmail.com',   smtp: 'smtp.gmail.com' },
      'gmx.net':      { imap: 'imap.gmx.net',      smtp: 'mail.gmx.net' },
      'gmx.de':       { imap: 'imap.gmx.net',      smtp: 'mail.gmx.net' },
      'outlook.com':  { imap: 'outlook.office365.com', smtp: 'smtp.office365.com' },
      'hotmail.com':  { imap: 'outlook.office365.com', smtp: 'smtp.office365.com' },
      'yahoo.com':    { imap: 'imap.mail.yahoo.com',   smtp: 'smtp.mail.yahoo.com' },
    };

    const preset = known[domain];
    if (preset) {
      imapHost = preset.imap;
      smtpHost = preset.smtp;
    } else {
      imapHost = `imap.${domain}`;
      smtpHost = `smtp.${domain}`;
      showAdvanced = true;
    }
  }

  async function handleLogin() {
    if (!imapHost || !smtpHost) inferHosts();

    error = '';
    loading = true;

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user: email,
          password: password,
          imap_host: imapHost,
          smtp_host: smtpHost,
        }),
      });

      if (res.ok) {
        goto('/');
      } else {
        const data = await res.json();
        error = data.error ?? 'Login failed';
      }
    } catch {
      error = 'Could not reach server';
    } finally {
      loading = false;
    }
  }
</script>

<svelte:head>
  <title>Sign in — Mail</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link
    href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist+Mono:wght@400;500&display=swap"
    rel="stylesheet"
  />
</svelte:head>

<div class="min-h-screen bg-[#0c0c0e] flex items-center justify-center px-4">

  <!-- Background texture -->
  <div
    class="pointer-events-none fixed inset-0 opacity-[0.03]"
    style="background-image: url('data:image/svg+xml,%3Csvg width=&quot;60&quot; height=&quot;60&quot; viewBox=&quot;0 0 60 60&quot; xmlns=&quot;http://www.w3.org/2000/svg&quot;%3E%3Cg fill=&quot;none&quot; fill-rule=&quot;evenodd&quot;%3E%3Cg fill=&quot;%23ffffff&quot;%3E%3Cpath d=&quot;M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z&quot;/%3E%3C/g%3E%3C/g%3E%3C/svg%3E');"
  ></div>

  <div class="w-full max-w-sm animate-[fadeUp_0.5s_ease_both]">

    <!-- Logo mark -->
    <div class="mb-10 text-center">
      <div class="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[#1a1a1e] border border-white/10 mb-4 shadow-[0_0_30px_rgba(251,191,36,0.08)]">
        <svg class="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
        </svg>
      </div>
      <h1 class="text-white/90 text-2xl leading-tight" style="font-family: 'Instrument Serif', serif;">
        Sign in to your mail
      </h1>
      <p class="text-white/30 text-sm mt-1" style="font-family: 'Geist Mono', monospace;">
        IMAP · SMTP
      </p>
    </div>

    <!-- Card -->
    <div class="bg-[#131316] border border-white/[0.07] rounded-2xl p-6 shadow-[0_24px_64px_rgba(0,0,0,0.5)]">

      <div class="space-y-4">

        <!-- Email -->
        <div>
          <label class="block text-xs text-white/40 mb-1.5 tracking-widest uppercase" style="font-family: 'Geist Mono', monospace;">
            Email
          </label>
          <input
            type="email"
            bind:value={email}
            onblur={inferHosts}
            placeholder="you@example.com"
            autocomplete="email"
            class="w-full bg-white/4 border border-white/8 rounded-lg px-3.5 py-2.5 text-white/80 text-sm placeholder:text-white/20 focus:outline-none focus:border-amber-400/40 focus:bg-white/[0.06] transition-all"
            style="font-family: 'Geist Mono', monospace;"
          />
        </div>

        <!-- Password -->
        <div>
          <label class="block text-xs text-white/40 mb-1.5 tracking-widest uppercase" style="font-family: 'Geist Mono', monospace;">
            Password
          </label>
          <input
            type="password"
            bind:value={password}
            placeholder="••••••••••"
            autocomplete="current-password"
            class="w-full bg-white/4 border border-white/8 rounded-lg px-3.5 py-2.5 text-white/80 text-sm placeholder:text-white/20 focus:outline-none focus:border-amber-400/40 focus:bg-white/[0.06] transition-all"
            style="font-family: 'Geist Mono', monospace;"
          />
        </div>

        <!-- Advanced toggle -->
        <button
          type="button"
          onclick={() => (showAdvanced = !showAdvanced)}
          class="flex items-center gap-1.5 text-xs text-white/30 hover:text-white/60 transition-colors"
          style="font-family: 'Geist Mono', monospace;"
        >
          <svg
            class="w-3 h-3 transition-transform duration-200 {showAdvanced ? 'rotate-90' : ''}"
            fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
          Server settings
          {#if imapHost && !showAdvanced}
            <span class="text-amber-400/60 ml-1">· {imapHost}</span>
          {/if}
        </button>

        <!-- Advanced fields -->
        {#if showAdvanced}
          <div class="space-y-3 pt-1 border-t border-white/6" style="animation: fadeDown 0.2s ease both">
            <div>
              <label class="block text-xs text-white/40 mb-1.5 tracking-widest uppercase" style="font-family: 'Geist Mono', monospace;">
                IMAP Host
              </label>
              <input
                type="text"
                bind:value={imapHost}
                placeholder="imap.example.com"
                class="w-full bg-white/4 border border-white/8 rounded-lg px-3.5 py-2.5 text-white/80 text-sm placeholder:text-white/20 focus:outline-none focus:border-amber-400/40 focus:bg-white/[0.06] transition-all"
                style="font-family: 'Geist Mono', monospace;"
              />
            </div>
            <div>
              <label class="block text-xs text-white/40 mb-1.5 tracking-widest uppercase" style="font-family: 'Geist Mono', monospace;">
                SMTP Host
              </label>
              <input
                type="text"
                bind:value={smtpHost}
                placeholder="smtp.example.com"
                class="w-full bg-white/4 border border-white/8 rounded-lg px-3.5 py-2.5 text-white/80 text-sm placeholder:text-white/20 focus:outline-none focus:border-amber-400/40 focus:bg-white/[0.06] transition-all"
                style="font-family: 'Geist Mono', monospace;"
              />
            </div>
          </div>
        {/if}

        <!-- Error -->
        {#if error}
          <div class="flex items-start gap-2 bg-red-500/8 border border-red-500/20 rounded-lg px-3.5 py-2.5">
            <svg class="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <p class="text-red-400 text-xs leading-relaxed" style="font-family: 'Geist Mono', monospace;">{error}</p>
          </div>
        {/if}

        <!-- Submit -->
        <button
          type="button"
          onclick={handleLogin}
          disabled={loading || !email || !password}
          class="w-full bg-amber-400 hover:bg-amber-300 disabled:opacity-30 disabled:cursor-not-allowed text-black font-medium text-sm rounded-lg px-4 py-2.5 transition-all duration-150 active:scale-[0.98] shadow-[0_4px_20px_rgba(251,191,36,0.2)] hover:shadow-[0_4px_28px_rgba(251,191,36,0.35)] mt-1"
          style="font-family: 'Geist Mono', monospace;"
        >
          {#if loading}
            <span class="inline-flex items-center gap-2">
              <svg class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              Connecting...
            </span>
          {:else}
            Sign in
          {/if}
        </button>

      </div>
    </div>

    <!-- Footer note -->
    <p class="text-center text-white/20 text-xs mt-6 leading-relaxed" style="font-family: 'Geist Mono', monospace;">
      Credentials are verified directly against<br/>your mail server. Nothing is stored.
    </p>

  </div>
</div>



<style lang="postcss">
    @reference "tailwindcss";
    :global(html) {
        background-color: theme(--color-gray-100);
    }

  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes fadeDown {
    from { opacity: 0; transform: translateY(-6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  input:-webkit-autofill,
  input:-webkit-autofill:focus {
    -webkit-box-shadow: 0 0 0 100px #1a1a1e inset;
    -webkit-text-fill-color: rgba(255,255,255,0.8);
    caret-color: rgba(255,255,255,0.8);
  }
</style>