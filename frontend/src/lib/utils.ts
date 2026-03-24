import he from "he";

export function formatSender(sender: string): string {
  return sender.slice(sender.indexOf("<") + 1, sender.indexOf(">"));
}


function extractText(html: string): string {
  if (typeof document !== "undefined") {
    const div = document.createElement("div");
    div.innerHTML = html;
    return div.textContent ?? "";
  }
  const stripped = html.replace(/<[^>]+>/g, "");
  return he.decode(stripped);
}

function cleanMarkdownJunk(text: string): string {
  // Remove markdown image links: ![alt](url)
  text = text.replace(/!\[[^\]]*\]\([^)]+\)/g, "");

  // Remove markdown links: [text](url) → keep text only
  // \S+ was wrongly eating the closing ) — use [^)]+ instead
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");

  // Remove bare URLs in brackets: [https://...]
  // \S+ was eating the closing ] — use [^\]]+ instead
  text = text.replace(/\[["']?https?:\/\/[^\]]+\]/g, "");

  // Remove "text [url]" patterns (e.g. "English [https://...]")
  text = text.replace(/\b\S+\s+\[https?:\/\/[^\]]+\]/g, "");

  // Remove any remaining bare URLs (including those prefixed with a quote)
  text = text.replace(/["']?https?:\/\/\S+/g, "");

  // Remove language navigation lines
  const langPattern = /^\s*(Previous|Next) group of languages\s*$/gim;
  text = text.replace(langPattern, "");

  // Remove lines that are just a language name (nav boilerplate)
  const languages = "English|Deutsch|Türkçe|العربية|Polski|Español|Русский|Français|Italiano|Українська|עברית|Shqip|Română";
  text = text.replace(new RegExp(`^\\s*(${languages})\\s*$`, "gm"), "");

  // Remove leftover empty brackets and stray punctuation lines
  text = text.replace(/\[\s*\]/g, "");
  text = text.replace(/^\s*[*|"'\[\]\s]+\s*$/gm, "");

  return text;
}

export function cleanEmailBody(emailBody: string): string {
  const isHtml = /<[a-z][\s\S]*>/i.test(emailBody);

  if (isHtml) {
    emailBody = emailBody.replace(/<(style|script)[^>]*>.*?<\/\1>/gis, "");
    emailBody = emailBody.replace(/<!--.*?-->/gs, "");
    emailBody = emailBody.replace(/<\/?(br\s*\/?|p|div|tr|li|h[1-6]|blockquote|pre)[^>]*>/gi, "\n");
    emailBody = extractText(emailBody);
  } else {
    emailBody = cleanMarkdownJunk(emailBody);
  }

  // Remove non-printable / zero-width / BOM characters
  emailBody = emailBody.replace(
    /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\ufeff\u200b-\u200d\u2028\u2029]/g,
    ""
  );

  // Collapse spaces/tabs
  emailBody = emailBody.replace(/[ \t]+/g, " ");

  // Collapse 3+ newlines into 2
  emailBody = emailBody.replace(/\n{3,}/g, "\n\n");

  return emailBody.trim();
}
