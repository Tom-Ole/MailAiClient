from bs4 import BeautifulSoup
import re

def clean_email_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all([
        "script", "style", "head", "meta", "link",
        "noscript", "iframe", "object", "embed", "footer", "header", "nav", "aside"
    ]):
        tag.decompose()

    for img in soup.find_all("img"):
        w = img.get("width", "")
        h = img.get("height", "")
        try:
            if int(w) <= 3 or int(h) <= 3:
                img.decompose()
                continue
        except (ValueError, TypeError):
            pass
        # replace remaining images with their alt text if available
        alt = img.get("alt", "").strip()
        img.replace_with(f"[Image: {alt}]" if alt else "")

    for tag in soup.find_all(style=re.compile(
        r"display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0|"
        r"font-size\s*:\s*0|max-height\s*:\s*0|overflow\s*:\s*hidden",
        re.IGNORECASE
    )):
        tag.decompose()

    BOILERPLATE_PATTERNS = [
        r"unsubscribe",
        r"opt[- ]?out",
        r"view\s+(this\s+)?email\s+in\s+(your\s+)?browser",
        r"if you (can't|cannot|can not) see this",
        r"add us to your address book",
        r"copyright\s+©?\s*\d{4}",
        r"all rights reserved",
        r"privacy policy",
        r"terms (of (service|use))?",
        r"sent (to|from|by)",
        r"mailing (list|address)",
    ]
    boilerplate_re = re.compile("|".join(BOILERPLATE_PATTERNS), re.IGNORECASE)

    for tag in soup.find_all(string=boilerplate_re):
        parent = tag.parent
        if parent:
            parent.decompose()

    text = soup.get_text(separator="\n")

    lines = [line.strip() for line in text.splitlines()]
    lines = [l for l in lines if l]                
    lines = [l for l in lines if len(l) > 3]
    text = "\n".join(lines)

    text = re.sub(r"\n{3,}", "\n\n", text)

    text = re.sub(r"([^\w\s])\1{3,}", "", text)

    return text.strip()