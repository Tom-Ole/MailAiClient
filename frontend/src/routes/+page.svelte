<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { decodeUTF7 } from "$lib/utils";

  // ── Types ────────────────────────────────────────────────────────────────
  type Folder = {
    name: string;
    display_name: string;
    unread_count: number;
    total_count: number;
    flags: string[];
  };

  type MailSummary = {
    uid: string;
    message_id: string;
    sender: string;
    receiver: string;
    subject: string;
    date: string;
    is_read: boolean;
    is_flagged: boolean;
    has_attachments: boolean;
    folder: string;
  };

  type MailFull = MailSummary & {
    cc: string;
    body_html: string;
    body_plain: string;
    timezone: string;
  };

  // ── State ────────────────────────────────────────────────────────────────
  let folders = $state<Folder[]>([]);
  let mails = $state<MailSummary[]>([]);
  let activeMail = $state<MailFull | null>(null);
  let activeFolder = $state("INBOX");
  let selected = $state<Set<string>>(new Set());
  let searchQuery = $state("");
  let searching = $state(false);
  let loadingMails = $state(true);
  let loadingMail = $state(false);
  let composing = $state(false);
  let page_num = $state(1);

  let textSummary = $state("");

  // ── Folder icon map ──────────────────────────────────────────────────────
  function folderIcon(name: string): string {
    const n = name.toLowerCase();
    if (n.includes("inbox"))
      return "M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z";
    if (n.includes("sent")) return "M12 19l9 2-9-18-9 18 9-2zm0 0v-8";
    if (n.includes("draft"))
      return "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z";
    if (n.includes("trash") || n.includes("deleted"))
      return "M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16";
    if (n.includes("spam") || n.includes("junk"))
      return "M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636";
    if (n.includes("archive"))
      return "M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4";
    if (n.includes("star") || n.includes("flagged"))
      return "M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z";
    return "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z";
  }

  // ── Sender display ───────────────────────────────────────────────────────
  function decodeMimeHeader(str: string): string {
    if (!str) return "";

    return (
      str
        // decode =?UTF-8?Q?...?=
        .replace(/=\?UTF-8\?Q\?(.+?)\?=/gi, (_, text) =>
          text
            .replace(/_/g, " ")
            .replace(/=([A-F0-9]{2})/gi, (_: unknown, hex: string) =>
              String.fromCharCode(parseInt(hex, 16)),
            ),
        )
        // decode =?UTF-8?B?...?=
        .replace(/=\?UTF-8\?B\?(.+?)\?=/gi, (_, b64) => atob(b64))
    );
  }

  function senderName(raw: string): string {
    if (!raw) return "-";

    raw = decodeMimeHeader(raw).trim();

    // Extract name before <
    const namePart = raw.split("<")[0].trim();

    // Remove quotes
    const clean = namePart.replace(/^"|"$/g, "").trim();

    if (clean && clean !== ",") return clean;

    // fallback → email
    const emailMatch = raw.match(/<(.+?)>/);
    if (emailMatch) {
      return emailMatch[1].split("@")[0];
    }

    return "-";
  }

  function senderInitial(raw: string): string {
    const name = senderName(raw);
    const c = name.trim()[0];
    return c && /[a-zA-Z0-9]/.test(c) ? c.toUpperCase() : "?";
  }

  function hasCC(cc: string | null | undefined): boolean {
    if (!cc) return false;
    const cleaned = cc.trim();
    return (
      cleaned !== "" &&
      cleaned !== "," &&
      cleaned !== "undisclosed-recipients:;"
    );
  }

  function formatDate(raw: string): string {
    if (!raw) return "";
    try {
      const d = new Date(raw);
      const now = new Date();
      const isToday = d.toDateString() === now.toDateString();
      if (isToday)
        return d.toLocaleTimeString("de-DE", {
          hour: "2-digit",
          minute: "2-digit",
        });
      const diffDays = (now.getTime() - d.getTime()) / 86400000;
      if (diffDays < 7)
        return d.toLocaleDateString("de-DE", { weekday: "short" });
      return d.toLocaleDateString("de-DE", {
        day: "2-digit",
        month: "2-digit",
      });
    } catch {
      return raw.slice(0, 10);
    }
  }

  // ── API calls ────────────────────────────────────────────────────────────
  async function loadFolders() {
    const res = await fetch("/api/folders");
    if (res.ok) {
      const data = await res.json();
      folders = data.folders;
    }
  }

  async function loadMails(folder = activeFolder, p = 1) {
    loadingMails = true;
    selected = new Set();
    const res = await fetch(
      `/api/mail?folder=${encodeURIComponent(folder)}&page=${p}&batchSize=50`,
    );
    if (res.ok) {
      const data = await res.json();
      mails = data.mails;
    }
    loadingMails = false;
  }

  async function openMail(uid: string) {
    if (activeMail?.uid === uid) return;
    loadingMail = true;
    activeMail = null;
    const res = await fetch(
      `/api/mail/${uid}?folder=${encodeURIComponent(activeFolder)}`,
    );
    if (res.ok) {
      activeMail = await res.json();
      // mark read locally
      mails = mails.map((m) => (m.uid === uid ? { ...m, is_read: true } : m));

      textSummary = "Generating Summary..."
      loadSummary(uid);


    }
    loadingMail = false;
  }

  async function loadSummary(uid: string) {
    const res = await fetch(`/api/mail/${uid}/summary`);

    if (res.ok) {
      const data = await res.json();
      textSummary = data.summary;
    } else {
      textSummary = "";
    }
  }

  async function doSearch() {
    if (!searchQuery.trim()) {
      loadMails();
      return;
    }
    searching = true;
    loadingMails = true;
    const res = await fetch(
      `/api/mail/search?q=${encodeURIComponent(searchQuery)}&folder=${encodeURIComponent(activeFolder)}`,
    );
    if (res.ok) {
      const data = await res.json();
      mails = data.mails;
    }
    loadingMails = false;
    searching = false;
  }

  async function deleteMail(uid: string) {
    await fetch(`/api/mail/${uid}?folder=${encodeURIComponent(activeFolder)}`, {
      method: "DELETE",
    });
    mails = mails.filter((m) => m.uid !== uid);
    if (activeMail?.uid === uid) activeMail = null;
  }

  async function deleteSelected() {
    await Promise.all([...selected].map((uid) => deleteMail(uid)));
    selected = new Set();
  }

  async function toggleFlag(uid: string, current: boolean) {
    await fetch(`/api/mail/${uid}?folder=${encodeURIComponent(activeFolder)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_flagged: !current }),
    });
    mails = mails.map((m) =>
      m.uid === uid ? { ...m, is_flagged: !current } : m,
    );
    if (activeMail?.uid === uid)
      activeMail = { ...activeMail, is_flagged: !current };
  }

  function selectFolder(name: string) {
    activeFolder = name;
    activeMail = null;
    searchQuery = "";
    loadMails(name);
  }

  function toggleSelect(uid: string) {
    const s = new Set(selected);
    s.has(uid) ? s.delete(uid) : s.add(uid);
    selected = s;
  }

  function selectAll() {
    selected =
      selected.size === mails.length
        ? new Set()
        : new Set(mails.map((m) => m.uid));
  }

  onMount(() => {
    loadFolders();
    loadMails();
  });
</script>

<svelte:head>
  <title>Mail</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link
    href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist+Mono:wght@300;400;500&display=swap"
    rel="stylesheet"
  />
</svelte:head>

<!-- Root shell -->
<div
  class="h-screen w-screen flex flex-col bg-[#0c0c0e] overflow-hidden"
  style="font-family: 'Geist Mono', monospace;"
>
  <!-- ── TOP BAR ─────────────────────────────────────────────────────────── -->
  <header
    class="h-12 shrink-0 flex items-center gap-1 px-3 border-b border-white/6 bg-[#0e0e11]"
  >
    <!-- Logo -->
    <div class="flex items-center gap-2 mr-3 pr-3 border-r border-white/6">
      <div
        class="w-6 h-6 rounded-md bg-amber-400/10 flex items-center justify-center"
      >
        <svg
          class="w-3.5 h-3.5 text-amber-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
          />
        </svg>
      </div>
      <span class="text-white/50 text-xs tracking-widest uppercase">Mail</span>
    </div>

    <!-- Compose -->
    <button
      onclick={() => (composing = true)}
      class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-black text-xs font-medium transition-all active:scale-95 shadow-[0_2px_12px_rgba(251,191,36,0.25)]"
    >
      <svg
        class="w-3.5 h-3.5"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M12 4v16m8-8H4"
        />
      </svg>
      Send
    </button>

    <!-- Divider -->
    <div class="w-px h-5 bg-white/6 mx-1"></div>

    <!-- Select all -->
    <button
      onclick={selectAll}
      title="Select all"
      class="toolbar-btn {selected.size === mails.length && mails.length > 0
        ? 'text-amber-400'
        : ''}"
    >
      <svg
        class="w-4 h-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    </button>

    <!-- Refresh -->
    <button onclick={() => loadMails()} title="Refresh" class="toolbar-btn">
      <svg
        class="w-4 h-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="1.5"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
        />
      </svg>
    </button>

    <!-- Delete selected -->
    {#if selected.size > 0}
      <button
        onclick={deleteSelected}
        title="Delete selected"
        class="toolbar-btn text-red-400/70 hover:text-red-400"
      >
        <svg
          class="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
          />
        </svg>
        <span class="text-xs">{selected.size}</span>
      </button>
    {/if}

    <!-- Divider -->
    <div class="w-px h-5 bg-white/6 mx-1"></div>

    <!-- Mail actions (visible when mail open) -->
    {#if activeMail}
      <button
        onclick={() => toggleFlag(activeMail!.uid, activeMail!.is_flagged)}
        title="Flag"
        class="toolbar-btn {activeMail.is_flagged ? 'text-amber-400' : ''}"
      >
        <svg
          class="w-4 h-4"
          fill={activeMail.is_flagged ? "currentColor" : "none"}
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M3 3v18m0-13.5l4.5-3 4.5 3 4.5-3 4.5 3V18l-4.5-3-4.5 3-4.5-3L3 18"
          />
        </svg>
      </button>

      <button
        onclick={() => deleteMail(activeMail!.uid)}
        title="Delete"
        class="toolbar-btn hover:text-red-400"
      >
        <svg
          class="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
          />
        </svg>
      </button>

      <button title="Reply" class="toolbar-btn">
        <svg
          class="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3"
          />
        </svg>
      </button>

      <button title="Forward" class="toolbar-btn">
        <svg
          class="w-4 h-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M15 15l6-6m0 0l-6-6m6 6H9a6 6 0 000 12h3"
          />
        </svg>
      </button>
    {/if}

    <!-- Search - pushed right -->
    <div
      class="ml-auto flex items-center gap-2 bg-white/4 border border-white/[0.07] rounded-lg px-3 py-1.5 w-64 focus-within:border-amber-400/30 transition-colors"
    >
      <svg
        class="w-3.5 h-3.5 text-white/30 shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        stroke-width="2"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
        />
      </svg>
      <input
        type="text"
        placeholder="Search mail…"
        bind:value={searchQuery}
        onkeydown={(e) => e.key === "Enter" && doSearch()}
        class="bg-transparent text-white/70 text-xs placeholder:text-white/20 focus:outline-none w-full"
      />
      {#if searchQuery}
        <button
          onclick={() => {
            searchQuery = "";
            loadMails();
          }}
          class="text-white/20 hover:text-white/50 transition-colors"
        >
          <svg
            class="w-3 h-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      {/if}
    </div>

    <!-- User -->
    <div class="ml-3 pl-3 border-l border-white/6">
      <button
        class="w-7 h-7 rounded-full bg-amber-400/20 border border-amber-400/30 flex items-center justify-center text-amber-400 text-xs font-medium hover:bg-amber-400/30 transition-colors"
      >
        {($page.data.user?.user ?? "U")[0].toUpperCase()}
      </button>
    </div>
  </header>

  <!-- ── BODY (sidebar + list + viewer) ─────────────────────────────────── -->
  <div class="flex flex-1 min-h-0">
    <!-- ── LEFT SIDEBAR ──────────────────────────────────────────────────── -->
    <aside
      class="w-52 shrink-0 flex flex-col border-r border-white/6 bg-[#0e0e11] py-3 overflow-y-auto"
    >
      <p class="px-4 text-[10px] text-white/20 uppercase tracking-widest mb-2">
        Folders
      </p>

      {#if folders.length === 0}
        {#each Array(6) as _}
          <div class="mx-3 mb-1 h-7 rounded-lg bg-white/3 animate-pulse"></div>
        {/each}
      {:else}
        {#each folders as folder}
          <button
            onclick={() => selectFolder(folder.name)}
            class="group flex items-center gap-2.5 mx-2 px-2.5 py-1.5 rounded-lg text-left transition-all
              {activeFolder === folder.name
              ? 'bg-amber-400/10 text-amber-400'
              : 'text-white/40 hover:text-white/70 hover:bg-white/4'}"
          >
            <svg
              class="w-3.5 h-3.5 shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d={folderIcon(folder.name)}
              />
            </svg>
            <span class="text-xs truncate flex-1"
              >{decodeUTF7(folder.display_name)}</span
            >
            {#if folder.unread_count > 0}
              <span
                class="text-[10px] px-1.5 py-0.5 rounded-full
                {activeFolder === folder.name
                  ? 'bg-amber-400/20 text-amber-400'
                  : 'bg-white/6 text-white/30'}"
              >
                {folder.unread_count}
              </span>
            {/if}
          </button>
        {/each}
      {/if}

      <!-- Bottom: user info -->
      <div class="mt-auto pt-3 mx-3 border-t border-white/5">
        <p class="text-[10px] text-white/20 truncate">
          {$page.data.user?.user ?? ""}
        </p>
        <a
          href="/api/auth/logout"
          class="text-[10px] text-white/20 hover:text-red-400/70 transition-colors mt-0.5 block"
          onclick={async () => {
            await fetch("/api/auth/logout", { method: "POST" });
            window.location.href = "/auth";
          }}
        >
          Sign out
        </a>
      </div>
    </aside>

    <!-- ── MAIL LIST ──────────────────────────────────────────────────────── -->
    <section
      class="w-80 shrink-0 flex flex-col border-r border-white/6 overflow-hidden"
    >
      <!-- List header -->
      <div
        class="px-4 py-2.5 border-b border-white/5 flex items-center justify-between shrink-0"
      >
        <div>
          <h2
            class="text-white/80 text-sm"
            style="font-family: 'Instrument Serif', serif;"
          >
            {searching ? "Results" : activeFolder}
          </h2>
          {#if !loadingMails}
            <p class="text-[10px] text-white/20">{mails.length} messages</p>
          {/if}
        </div>
        {#if selected.size > 0}
          <span class="text-[10px] text-amber-400/70"
            >{selected.size} selected</span
          >
        {/if}
      </div>

      <!-- Mail rows -->
      <div class="flex-1 overflow-y-auto">
        {#if loadingMails}
          {#each Array(8) as _}
            <div class="px-4 py-3 border-b border-white/4">
              <div
                class="h-2.5 w-24 bg-white/5 rounded animate-pulse mb-2"
              ></div>
              <div
                class="h-2 w-48 bg-white/4 rounded animate-pulse mb-1.5"
              ></div>
              <div class="h-2 w-36 bg-white/3 rounded animate-pulse"></div>
            </div>
          {/each}
        {:else if mails.length === 0}
          <div
            class="flex flex-col items-center justify-center h-full text-white/20 gap-2"
          >
            <svg
              class="w-8 h-8 opacity-30"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
              />
            </svg>
            <p class="text-xs">No messages</p>
          </div>
        {:else}
          {#each mails as mail (mail.uid)}
            <button
              onclick={() => openMail(mail.uid)}
              class="group w-full text-left px-4 py-3 border-b border-white/4 transition-all relative
                {activeMail?.uid === mail.uid
                ? 'bg-amber-400/7 border-l-2 border-l-amber-400'
                : 'hover:bg-white/3 border-l-2 border-l-transparent'}"
            >
              <!-- Unread dot -->
              {#if !mail.is_read}
                <span
                  class="absolute left-1.5 top-1/2 -translate-y-1/2 w-1 h-1 rounded-full bg-amber-400"
                ></span>
              {/if}

              <!-- Checkbox -->
              <div class="flex items-start gap-2.5">
                <div
                  role="checkbox"
                  aria-checked={selected.has(mail.uid)}
                  tabindex="0"
                  onclick={() => toggleSelect(mail.uid)}
                  onkeydown={(e) => e.key === " " && toggleSelect(mail.uid)}
                  class="mt-0.5 w-3.5 h-3.5 rounded border shrink-0 flex items-center justify-center transition-all cursor-pointer
                    {selected.has(mail.uid)
                    ? 'bg-amber-400 border-amber-400'
                    : 'border-white/12 opacity-0 group-hover:opacity-100'}"
                >
                  {#if selected.has(mail.uid)}
                    <svg
                      class="w-2.5 h-2.5 text-black"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      stroke-width="3"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                  {/if}
                </div>

                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between gap-2 mb-1">
                    <span
                      class="text-xs truncate {mail.is_read
                        ? 'text-white/50'
                        : 'text-white/85 font-medium'}"
                    >
                      {senderName(mail.sender)}
                    </span>
                    <span class="text-[10px] text-white/25 shrink-0"
                      >{formatDate(mail.date)}</span
                    >
                  </div>
                  <p
                    class="text-xs truncate {mail.is_read
                      ? 'text-white/30'
                      : 'text-white/60'} mb-0.5"
                  >
                    {mail.subject || "(no subject)"}
                  </p>
                  <div class="flex items-center gap-1.5">
                    {#if mail.is_flagged}
                      <svg
                        class="w-3 h-3 text-amber-400/70"
                        fill="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          d="M3 3v18m0-13.5l4.5-3 4.5 3 4.5-3 4.5 3V18l-4.5-3-4.5 3-4.5-3L3 18"
                          stroke="currentColor"
                          stroke-width="1.5"
                          fill="none"
                        />
                      </svg>
                    {/if}
                    {#if mail.has_attachments}
                      <svg
                        class="w-3 h-3 text-white/20"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        stroke-width="1.5"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13"
                        />
                      </svg>
                    {/if}
                  </div>
                </div>
              </div>
            </button>
          {/each}
        {/if}
      </div>
    </section>

    <!-- ── RIGHT PANEL ────────────────────────────────────────────────────── -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Mail content (80%) -->
      <div class="flex flex-col min-h-0" style="flex: 8;">
        {#if loadingMail}
          <div class="flex-1 flex items-center justify-center">
            <svg
              class="w-5 h-5 text-amber-400/40 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              ></path>
            </svg>
          </div>
        {:else if activeMail}
          <!-- Mail header -->
          <div class="px-8 pt-7 pb-5 border-b border-white/5 shrink-0">
            <h1
              class="text-white/90 text-xl leading-snug mb-4"
              style="font-family: 'Instrument Serif', serif;"
            >
              {activeMail.subject || "(no subject)"}
            </h1>
            <div class="flex items-start justify-between gap-4">
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <div
                    class="w-7 h-7 rounded-full bg-amber-400/15 border border-amber-400/20 flex items-center justify-center text-amber-400 text-xs shrink-0"
                  >
                    {senderInitial(activeMail.sender)}
                  </div>
                  <div>
                    <p class="text-xs text-white/70">
                      {senderName(activeMail.sender)}
                    </p>
                    <p class="text-[10px] text-white/30">
                      {activeMail.sender.match(/<(.+)>/)?.[1] ??
                        activeMail.sender}
                    </p>
                  </div>
                </div>
                {#if hasCC(activeMail.cc)}
                  <p class="text-[10px] text-white/25 pl-9">
                    CC: {activeMail.cc}
                  </p>
                {/if}
              </div>
              <div class="text-right shrink-0">
                <p class="text-[10px] text-white/30">{activeMail.date}</p>
                {#if activeMail.has_attachments}
                  <a
                    href="/api/mail/{activeMail.uid}/attachments?folder={encodeURIComponent(
                      activeFolder,
                    )}"
                    class="text-[10px] text-amber-400/60 hover:text-amber-400 transition-colors mt-1 block"
                  >
                    Attachments ↗
                  </a>
                {/if}
              </div>
            </div>
          </div>

          <!-- Mail body -->
          <div class="flex-1 overflow-hidden flex flex-col">
            {#if activeMail.body_html}
              <!-- <div class="mail-body prose-sm">
                {@html activeMail.body_html}
              </div> -->
              <iframe
                srcdoc={`<!DOCTYPE html>
                            <html>
                            <head>
                            <meta charset="utf-8">
                            <style>
                              html, body {
                                margin: 0;
                                background: #ffffff;
                                color: #111111;
                                font-family: sans-serif;
                                font-size: 14px;
                                line-height: 1.6;
                              }
                              img { max-width: 100%; }
                              a { color: #d97706; }
                            </style>
                            </head>
                            <body>${activeMail.body_html}</body>
                            </html>`
                        }
                sandbox="allow-same-origin allow-popups"
                class="w-full border-0"
                style="flex: 1; min-height: 0; height: 100%;"
                title="Mail body"
              >
              </iframe>
            {:else}
              <pre
                class="text-white/60 text-xs leading-relaxed whitespace-pre-wrap font-mono">{decodeUTF7(
                  activeMail.body_plain,
                )}</pre>
            {/if}
          </div>
        {:else}
          <!-- Empty state -->
          <div
            class="flex-1 flex flex-col items-center justify-center text-center gap-3 select-none"
          >
            <div
              class="w-14 h-14 rounded-2xl bg-white/3 border border-white/5 flex items-center justify-center"
            >
              <svg
                class="w-6 h-6 text-white/15"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="1"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
                />
              </svg>
            </div>
            <div>
              <p
                class="text-white/20 text-sm"
                style="font-family: 'Instrument Serif', serif; font-style: italic;"
              >
                Select a message to read
              </p>
              <p class="text-white/10 text-xs mt-1">
                {mails.length} messages in {activeFolder}
              </p>
            </div>
          </div>
        {/if}
      </div>

      <!-- Divider -->
      <div class="h-px bg-white/6 shrink-0"></div>

      <!-- Bottom panel (20%) - reserved -->
      <div
        class="shrink-0 bg-[#0e0e11] flex items-center justify-center"
        style="flex: 2;"
      >
        <p class="text-white/50 text-xs tracking-widest uppercase w-3/4 text-center">
          {#if textSummary != ""}
            {textSummary}
          {:else}
            No preview available
          {/if}
        </p>
      </div>
    </div>
  </div>
</div>

<style lang="postcss">
  @reference "tailwindcss";

  :global(body) {
    overflow: hidden;
  }

  /* Toolbar button base */
  :global(.toolbar-btn) {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.375rem;
    border-radius: 0.5rem;
    color: rgba(255, 255, 255, 0.35);
    transition:
      color 0.15s,
      background 0.15s;
  }
  :global(.toolbar-btn:hover) {
    color: rgba(255, 255, 255, 0.7);
    background: rgba(255, 255, 255, 0.04);
  }

  /* Sandboxed email HTML body */
  .mail-body {
    color: rgba(255, 255, 255, 0.65);
    font-size: 0.8rem;
    line-height: 1.7;
  }
  .mail-body :global(a) {
    color: #fbbf24;
    text-decoration: underline;
  }
  .mail-body :global(img) {
    max-width: 100%;
    border-radius: 0.5rem;
  }
  .mail-body :global(blockquote) {
    border-left: 2px solid rgba(255, 255, 255, 0.1);
    padding-left: 1rem;
    color: rgba(255, 255, 255, 0.3);
    margin: 0.5rem 0;
  }
  .mail-body :global(p) {
    margin-bottom: 0.75rem;
  }
  .mail-body :global(pre) {
    background: rgba(255, 255, 255, 0.04);
    padding: 0.75rem;
    border-radius: 0.5rem;
    overflow-x: auto;
  }
  .mail-body :global(table) {
    width: 100%;
    border-collapse: collapse;
  }
  .mail-body :global(td),
  .mail-body :global(th) {
    padding: 0.4rem 0.6rem;
    border: 1px solid rgba(255, 255, 255, 0.06);
  }
</style>
