---
name: block-push-main
enabled: true
event: bash
pattern: git push[^|]*\bmain\b
action: block
---

🚫 **Direct push to main blocked!**

This project requires all changes to `main` to go through pull requests.

**What to do instead:**

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Push your branch: `git push -u origin feature/your-feature`
3. Create a PR: `gh pr create --base main`

See AGENTS.md Git Rules for more details.
