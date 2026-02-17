How to add translations

1) Copy en.json
   - Create a new file in this folder named with a locale code.
     Examples: de.json, fr.json, es.json, it.json, nl.json

2) Translate values only
   - Keep the JSON keys exactly as they are.
   - Only change the string values (the text on the right side).

3) Keep valid JSON
   - Use double quotes for all strings.
   - Make sure commas are in the right places.
   - The file must be valid JSON (no comments).

4) Test in Home Assistant
   - Restart Home Assistant or reload the integration.
   - Switch the UI language to your new locale and verify names.

Notes
- If you add new keys in the future, update en.json first.
- You can copy en.json again and translate only the new keys.
