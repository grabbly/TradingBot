# 🔒 Git History Cleanup Guide - Remove Sensitive Data

## ⚠️ IMPORTANT: Execute BEFORE publishing repository!

If you've already committed files with secrets to Git, they need to be removed from history.

---

## 📋 What Was Found and Fixed

### ✅ Fixed Files (now safe):
- `check_portfolio.py` - removed hardcoded API keys
- `check_orders.py` - removed hardcoded API keys  
- `scripts/check_positions_alpaca.py` - removed hardcoded API keys
- `scripts/load_historical_data.py` - removed hardcoded DB password
- `scripts/backtest_golden_cross.py` - removed hardcoded DB password
- `scripts/backtest_weekly_ema.py` - removed hardcoded DB password
- `scripts/backtest_ema_strategy.py` - removed hardcoded DB password
- `scripts/plot_ema.py` - removed hardcoded DB password and IP
- `web/app.py` - removed hardcoded DB password
- `.env` - cleaned of real data (now template)
- `.env.example` - cleaned of real passwords
- `.gitignore` - updated to protect sensitive files

### 🚨 Sensitive Data That Was in Repository:
- Alpaca API keys: `PKX2Y2J57QRKG5HVGZ4IRKG7TG` and secret
- Finnhub API key: `d5vp0lhr01qihi8n877gd5vp0lhr01qihi8n8780`
- PostgreSQL password: `n8n_secure_pass_2024`
- Local IP: `192.168.1.3`
- Files in `.docs/` with potential secrets

---

## 🛠️ Git History Cleanup Steps

### Option 1: BFG Repo-Cleaner (recommended - fast and simple)

```bash
# 1. Install BFG (if not already installed)
brew install bfg   # macOS
# or download from https://rtyley.github.io/bfg-repo-cleaner/

# 2. Create list of secrets to remove
cat > secrets.txt << 'EOF'
PKX2Y2J57QRKG5HVGZ4IRKG7TG
GzgSzBh7YKE4jagtgqRo6SxhGLZK9BXQoj4d6Fzqj2wx
d5vp0lhr01qihi8n877gd5vp0lhr01qihi8n8780
n8n_secure_pass_2024
n8n_secure_pass_202
192.168.1.3
EOF

# 3. Create repository backup
cd /Users/gabby/git
cp -r TradingBot TradingBot.backup

# 4. Run cleanup
cd TradingBot
bfg --replace-text secrets.txt

# 5. Clean history and verify
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 6. Delete secrets file
rm ../secrets.txt

# 7. Verify secrets are gone
git log --all --full-history -- "*" | grep -i "PKX2Y2J57QRKG5HVGZ4IRKG7TG" || echo "✅ Secrets removed"
```

### Option 2: git-filter-repo (more flexible)

```bash
# 1. Install git-filter-repo
brew install git-filter-repo   # macOS
# or: pip3 install git-filter-repo

# 2. Create backup
cd /Users/gabby/git
cp -r TradingBot TradingBot.backup

# 3. Remove files from history
cd TradingBot
git-filter-repo --invert-paths \
  --path .env \
  --path .docs/ \
  --force

# 4. Replace secrets in remaining files
git-filter-repo --replace-text <(cat << 'EOF'
PKX2Y2J57QRKG5HVGZ4IRKG7TG==>ALPACA_API_KEY_REMOVED
GzgSzBh7YKE4jagtgqRo6SxhGLZK9BXQoj4d6Fzqj2wx==>ALPACA_SECRET_REMOVED
d5vp0lhr01qihi8n877gd5vp0lhr01qihi8n8780==>FINNHUB_KEY_REMOVED
n8n_secure_pass_2024==>PASSWORD_REMOVED
192.168.1.3==>localhost
EOF
) --force
```

### Option 3: Start Fresh (safest for public repositories)

```bash
# 1. Save current code
cd /Users/gabby/git
cp -r TradingBot TradingBot.backup

# 2. Remove .git directory
cd TradingBot
rm -rf .git

# 3. Create new repository
git init
git add .
git commit -m "Initial commit - cleaned version"

# 4. Setup new remote (if needed)
# git remote add origin YOUR_NEW_REPO_URL
# git push -u origin main
```

---

## 🔐 After Cleanup: Mandatory Actions

### 1. Revoke All API Keys

#### Alpaca (CRITICAL!)
1. Go to: https://app.alpaca.markets/paper/dashboard/overview
2. Delete old keys: `PKX2Y2J57QRKG5HVGZ4IRKG7TG`
3. Create new keys
4. Update `.env` locally (DO NOT commit!)

#### Finnhub
1. Go to: https://finnhub.io/dashboard
2. Revoke key: `d5vp0lhr01qihi8n877gd5vp0lhr01qihi8n8780`
3. Create new key
4. Update `.env` locally

### 2. Change PostgreSQL Password

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres

# Change password
ALTER USER n8n_user WITH PASSWORD 'your_new_secure_password';
\q

# Update .env locally
```

### 3. Configure .env for Work

```bash
# Copy template
cp .env .env.local

# Fill in .env with real values
nano .env

# Verify .env is in .gitignore
cat .gitignore | grep "^\.env$"
```

---

## ✅ Pre-Publication Verification

```bash
# 1. Check for sensitive data
git log --all --full-history --source --grep="PKX2Y2J57QRKG5HVGZ4IRKG7TG"
git log --all --full-history --source --grep="n8n_secure_pass"

# 2. Check all files in history
git grep -i "PKX2Y2J57QRKG5HVGZ4IRKG7TG" $(git rev-list --all)
git grep -i "n8n_secure_pass" $(git rev-list --all)

# 3. Verify .env not in git
git ls-files | grep "^\.env$" && echo "⚠️ .env in repository!" || echo "✅ .env not tracked"

# 4. Verify .docs not in git
git ls-files | grep "\.docs/" && echo "⚠️ .docs in repository!" || echo "✅ .docs not tracked"

# 5. Check .gitignore
cat .gitignore
```

---

## 📤 Publishing to GitHub

After cleanup and verification:

```bash
# 1. Create new repository on GitHub (via web interface)
#    DO NOT initialize with README if you already have local

# 2. Add remote
git remote add origin https://github.com/YOUR_USERNAME/TradingBot.git

# 3. Push (use --force only for new repository!)
git push -u origin main

# OR for existing repository AFTER cleanup:
# git push --force-with-lease origin main
```

---

## ⚠️ Important Reminders

1. **NEVER use `--force` push if someone has already cloned the repository!**
2. **After force push, all secrets MAY STILL be accessible** in old clones
3. **Revoking API keys is CRITICALLY IMPORTANT** even after history cleanup
4. **Use `.env` only locally**, never commit it
5. **Regularly verify** you don't accidentally add secrets

---

## 📚 Additional Resources

- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [git-filter-repo](https://github.com/newren/git-filter-repo)
- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Git Secrets Scanner](https://github.com/trufflesecurity/trufflehog)

---

## 🆘 If Secrets Are Already in Public Repository

1. **Immediately revoke ALL keys**
2. Change all passwords
3. Check Alpaca/Finnhub logs for suspicious activity
4. Delete repository from GitHub (if possible)
5. Create new repository with cleaned history
6. Notify team (if not working alone)

---

**Good luck! After completing all steps, your repository will be safe for publication.**
