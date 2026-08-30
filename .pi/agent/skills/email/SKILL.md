---
name: email
description: Use anytime email is mentioned or an email-related action is requested.
---

# Email rules

- Never send an email unless user explicitly asks to send, reply, or forward it.
- Never read emails unless user explicitly asks to read, search, fetch, or inspect them.
- `Dome` always means Gmail account whose address uses `dome.software`.
- `personal`, `purelymail`, `regular`, and similar terms mean Purelymail account.
- For every Purelymail outbound message, always use a custom `from` address on `gum.cx`.
- For replies, normally use recipient address they used to email us as custom `from`.
- If prompted to use any email address, generate one with:
  ```sh
  echo "$(nix run nixpkgs#diceware -- -n 1 | sed 's/[A-Z]/\\L&/gm')$(shuf -n 4 -i 0-9)" | tr -d "\\n"
  ```
  Prepend result to `@gum.cx`. Keep generated words inoffensive, nonpolitical, and noncontroversial.
- Purelymail display name is blank by default. Never use `Kaniel Kirby` unless user explicitly asks.
- Before Purelymail sending, verify `from` is present and ends in `@gum.cx`; otherwise stop and ask.
- Use `profile: "gmail"` for Dome and `profile: "purelymail"` for personal mail.
