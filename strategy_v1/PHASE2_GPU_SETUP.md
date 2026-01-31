# Phase 2: FinBERT GPU Server Setup Plan
**Server:** 192.168.1.3 (RTX 3060, 12GB VRAM)  
**User:** gabby  
**Status:** Planning - Nothing installed yet  
**Date:** 2026-01-08

---

## ⚠️ CRITICAL: Safety First!

### Rules:
1. ✅ **Always check before installing** anything
2. ✅ **Never delete** existing files without confirmation
3. ✅ **Backup** configuration before changes
4. ✅ **Test** in isolated environment first
5. ❌ **Never commit** passwords/keys to git

### Sensitive Data:
- **SSH credentials:** In `.env` file (NOT in git)
- **Sudo password:** In `.env` file (NOT in git)
- **Location:** `.env` is in `.gitignore` ✅

---

## 🔍 Step 0: Pre-Installation Audit (MANDATORY)

### Check what's already installed:
```bash
# Connect to server
ssh gabby@192.168.1.3

# Check Python version
python3 --version

# Check if CUDA installed
nvidia-smi

# Check existing Python packages
pip3 list | grep -E "(torch|transformers|flask|gunicorn)"

# Check running services
sudo systemctl list-units --type=service --state=running

# Check open ports
sudo netstat -tulpn | grep LISTEN

# Check disk space
df -h

# Check memory
free -h

# Exit
exit
```

**⚠️ STOP HERE - Review output before proceeding!**

---

## 📦 Step 1: Install FinBERT Dependencies (After approval)

### 1.1: PyTorch with CUDA support
```bash
# Check CUDA version first
nvidia-smi

# Install PyTorch for CUDA 11.8 (or matching version)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 1.2: Transformers library
```bash
pip3 install transformers accelerate
```

### 1.3: Flask for API server
```bash
pip3 install flask flask-cors python-dotenv
```

### 1.4: Production server
```bash
pip3 install gunicorn
```

---

## 🧪 Step 2: Test FinBERT (Isolated)

### Create test script:
```bash
# Create test directory
mkdir -p ~/finbert_test
cd ~/finbert_test

# Create test script
cat > test_finbert.py << 'EOF'
#!/usr/bin/env python3
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")

print("\nLoading FinBERT model...")
tokenizer = AutoTokenizer.from_pretrained('ProsusAI/finbert')
model = AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')

if torch.cuda.is_available():
    model = model.to('cuda')
    print("✅ Model loaded on GPU")
else:
    print("⚠️ Model loaded on CPU (slow!)")

# Test inference
text = "Apple stock rises on strong earnings report"
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
if torch.cuda.is_available():
    inputs = {k: v.to('cuda') for k, v in inputs.items()}

with torch.no_grad():
    outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

print(f"\nTest sentiment analysis:")
print(f"  Positive: {probs[0][0].item():.4f}")
print(f"  Negative: {probs[0][1].item():.4f}")
print(f"  Neutral:  {probs[0][2].item():.4f}")
print("\n✅ FinBERT test successful!")
EOF

chmod +x test_finbert.py
python3 test_finbert.py
```

**Expected output:** Model loads on GPU, sentiment scores look reasonable

---

## 🚀 Step 3: Deploy FinBERT API Service

### 3.1: Create service directory
```bash
# On server
mkdir -p ~/tradingbot/finbert_service
cd ~/tradingbot/finbert_service
```

### 3.2: Transfer files from Mac
```bash
# On Mac
scp finbert_service.py gabby@192.168.1.3:~/tradingbot/finbert_service/
scp .env gabby@192.168.1.3:~/tradingbot/finbert_service/
```

### 3.3: Create systemd service (optional - for auto-start)
```bash
# On server
sudo nano /etc/systemd/system/finbert-api.service

# Content:
[Unit]
Description=FinBERT Sentiment Analysis API
After=network.target

[Service]
Type=simple
User=gabby
WorkingDirectory=/home/gabby/tradingbot/finbert_service
ExecStart=/usr/bin/python3 finbert_service.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable finbert-api
sudo systemctl start finbert-api
sudo systemctl status finbert-api
```

---

## 🔧 Step 4: Test API Endpoint

### From Mac:
```bash
# Test health check
curl http://192.168.1.3:5001/health

# Test sentiment analysis
curl -X POST http://192.168.1.3:5001/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Apple stock rises on strong earnings"}'

# Expected response:
# {"sentiment": 0.85, "positive": 0.92, "negative": 0.02, "neutral": 0.06}
```

---

## 📊 Step 5: Performance Benchmarks

### Run benchmark:
```bash
# On server
cd ~/tradingbot/finbert_service
python3 benchmark_finbert.py

# Expected metrics:
# - Single inference: ~10-30ms on RTX 3060
# - Batch 32: ~100-200ms (5-10ms per text)
# - Memory usage: ~2-3GB VRAM
# - Max throughput: ~100-300 texts/second
```

---

## 🔒 Step 6: Security Hardening

### 6.1: Firewall rules
```bash
# Allow only from local network
sudo ufw allow from 192.168.1.0/24 to any port 5001
sudo ufw status
```

### 6.2: API authentication (optional)
- Add API key validation
- Rate limiting
- Request logging

---

## 📝 Rollback Plan

### If something goes wrong:

1. **Stop service:**
```bash
sudo systemctl stop finbert-api
```

2. **Uninstall packages:**
```bash
pip3 uninstall torch transformers flask -y
```

3. **Remove files:**
```bash
rm -rf ~/tradingbot/finbert_service
rm -rf ~/finbert_test
sudo rm /etc/systemd/system/finbert-api.service
sudo systemctl daemon-reload
```

4. **Restore original state** - Nothing broken!

---

## ✅ Verification Checklist

Before marking Phase 2 complete:

- [ ] Server audit completed and reviewed
- [ ] CUDA and PyTorch working on GPU
- [ ] FinBERT model loads successfully
- [ ] Test inference shows reasonable results
- [ ] API service responds to requests
- [ ] Performance benchmarks meet expectations (>50 texts/sec)
- [ ] Service auto-starts on reboot
- [ ] Firewall configured
- [ ] No existing services broken
- [ ] Backup of all config files taken

---

## 📞 Contact Info

**If issues arise:**
- Check logs: `sudo journalctl -u finbert-api -f`
- GPU status: `nvidia-smi`
- Service status: `sudo systemctl status finbert-api`
- Test locally: `python3 test_finbert.py`

---

## 🎯 Next Steps (After GPU setup)

1. **Task 2.2:** Fix EODHD API or migrate to alternative
2. **Task 2.3:** Re-run backtest with real sentiment
3. **Task 2.4:** Update n8n workflows to use GPU server

---

**Created:** 2026-01-08  
**Status:** Planning phase - awaiting server audit approval  
**Risk Level:** LOW (isolated installation, no deletions)
