# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email the maintainer directly
3. Include details about the vulnerability

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅        |

## Security Considerations

- This is an **educational simulation** — not a production system
- No real patient data should ever be stored
- API keys should never be committed to the repository
- Use `.env` files for secrets (excluded via `.gitignore`)
- The demo mode runs without any external API keys

## Dependencies

We regularly update dependencies to patch known vulnerabilities. Run:

```bash
pip install --upgrade -r backend/requirements.txt
npm audit fix --prefix frontend
```
