# 🚀 Quick Start: Preparing for Publication

## ✅ What's Already Done

The project has been **cleaned of sensitive data** and is ready for further preparation for publication:

### Fixed:
- ✅ Updated `.gitignore` - now protects `.env`, `.docs/`, `data/`, `reports/`
- ✅ All Python scripts use environment variables instead of hardcoded credentials
- ✅ `.env` file cleaned and turned into a template
- ✅ `.env.example` contains only placeholder values
- ✅ Created complete Git history cleanup instructions: `GIT_CLEANUP_GUIDE.md`

---

## ⚠️ MANDATORY BEFORE PUBLICATION

### 1️⃣ Revoke ALL API Keys

#### 🔑 Alpaca (CRITICAL!)
```
Old keys (LEAKED):
- API Key: PKX2Y2J57QRKG5HVGZ4IRKG7TG
- Secret: GzgSzBh7YKE4jagtgqRo6SxhGLZK9BXQoj4d6Fzqj2wx

Actions:
1. https://app.alpaca.markets/paper/dashboard/overview
2. Delete old keys
3. Create new keys
4. Update local .env file
```

#### 🔑 Finnhub
```
Old key (LEAKED): d5vp0lhr01qihi8n877gd5vp0lhr01qihi8n8780

Actions:
1. https://finnhub.io/dashboard
2. Revoke old key
3. Create new key
4. Update local .env file
```

### 2️⃣ Change PostgreSQL Password

```bash
psql -h localhost -U postgres
ALTER USER n8n_user WITH PASSWORD 'new_secure_password';
\q
```

### 3️⃣ Clean Git History

**Choose one method from `GIT_CLEANUP_GUIDE.md`:**

#### Quick method (recommended):
```bash
# Create backup
cp -r /Users/gabby/git/TradingBot /Users/gabby/git/TradingBot.backup

# Use BFG Repo-Cleaner
cd /Users/gabby/git/TradingBot
brew install bfg

# Create secrets list
cat > /tmp/secrets.txt << 'EOF'
PKX2Y2J57QRKG5HVGZ4IRKG7TG
GzgSzBh7YKE4jagtgqRo6SxhGLZK9BXQoj4d6Fzqj2wx
d5vp0lhr01qihi8n877gd5vp0lhr01qihi8n8780
n8n_secure_pass_2024
EOF

# Clean
bfg --replace-text /tmp/secrets.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
rm /tmp/secrets.txt
```

### 4️⃣ Verify No Secrets Remain

```bash
cd /Users/gabby/git/TradingBot

# Check current files
git grep -i "PKX2Y2J57QRKG5HVGZ4IRKG7TG" || echo "✅ OK"
git grep -i "n8n_secure_pass" || echo "✅ OK"

# Verify .env not in repository
git ls-files | grep "^\.env$" && echo "⚠️ PROBLEM!" || echo "✅ OK"

# Verify .docs not in repository
git ls-files | grep "\.docs/" && echo "⚠️ PROBLEM!" || echo "✅ OK"
```

---

## 📝 Local Environment Setup

After cleanup, create local `.env` file:

```bash
cd /Users/gabby/git/TradingBot

# Create .env from template
cp .env .env.local

# Edit and add real data
nano .env

# .env should contain:
# ALPACA_API_KEY=your_new_key
# ALPACA_SECRET_KEY=your_new_secret
# POSTGRES_PASSWORD=your_new_password
# FINNHUB_API_KEY=your_new_key
# etc.
```

⚠️ **NEVER commit the .env file!**

---

## 🌐 Publishing to GitHub

After completing all steps above:

```bash
cd /Users/gabby/git/TradingBot

# Add changes
git add .
git commit -m "Security: Remove hardcoded credentials, update to use environment variables"

# Create new repository on GitHub (via web)
# Then add remote:
git remote add origin https://github.com/YOUR_USERNAME/TradingBot.git

# Push (if this is a NEW repository)
git push -u origin main

# OR force push if you cleaned history (CAREFUL!)
# git push --force-with-lease origin main
```

---

## 📚 Important Files

- **`GIT_CLEANUP_GUIDE.md`** - Detailed Git history cleanup instructions
- **`.gitignore`** - Updated to protect sensitive data
- **`.env.example`** - Template for environment setup
- **`.env`** - Local file (DO NOT COMMIT!)

---

## 🔒 Pre-Publication Checklist

- [ ] Revoked Alpaca API keys
- [ ] Revoked Finnhub API key
- [ ] Changed PostgreSQL password
- [ ] Cleaned Git history (BFG or git-filter-repo)
- [ ] Verified no secrets: `git grep -i "PKX2Y2J"`
- [ ] `.env` file in `.gitignore` and not tracked
- [ ] `.docs/` directory in `.gitignore` and not tracked
- [ ] Created local `.env` with new credentials
- [ ] Tested scripts with new credentials

---

## ❓ Questions?

See **`GIT_CLEANUP_GUIDE.md`** for detailed instructions.

**Good luck! 🚀**
