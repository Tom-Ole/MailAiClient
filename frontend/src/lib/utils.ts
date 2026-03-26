export function decodeUTF7(input: string): string {
  return input.replace(/&([A-Za-z0-9+,]*)-/g, (_, encoded) => {
    if (encoded === "") return "&";

    // Convert modified Base64 (IMAP uses ',' instead of '/')
    const base64 = encoded.replace(/,/g, "/");

    // Decode base64 to bytes
    const binary = atob(base64);

    // Convert to UTF-16 string
    let result = "";
    for (let i = 0; i < binary.length; i += 2) {
      const charCode =
        (binary.charCodeAt(i) << 8) |
        (binary.charCodeAt(i + 1) || 0);
      result += String.fromCharCode(charCode);
    }

    return result;
  });
}