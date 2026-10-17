# 🔑 Real AI API Setup Guide

This guide shows you how to get **free API keys** for real AI responses in NexusAI.

## 🚀 Quick Start (Recommended: Groq)

**Groq is FREE, FAST, and gives you access to Llama 3.3 70B** - one of the best open-source models!

### Step 1: Get Groq API Key (2 minutes)

1. Go to: **https://console.groq.com/keys**
2. Sign up with Google/GitHub (free, no credit card needed)
3. Click "Create API Key"
4. Copy your key (starts with `gsk_...`)

### Step 2: Add to Your .env File

```bash
# Open backend/.env and add:
GROQ_API_KEY=gsk_your_actual_key_here
DEFAULT_LLM_PROVIDER=groq
```

### Step 3: Restart Server

```bash
cd backend
uvicorn app.main:app --reload
```

### Step 4: Test It! 🎉

Go to http://localhost:8000 and ask: **"What is machine learning?"**

You should get a **real AI response** from Llama 3.3!

---

## 🌟 Alternative Free Providers

### Option 1: OpenRouter (Multiple Free Models)

**Best for**: Trying different models without costs

1. Sign up: **https://openrouter.ai/keys**
2. Get your API key (free models don't require credits)
3. Add to `.env`:

```bash
OPENROUTER_API_KEY=sk-or-v1-your-key-here
DEFAULT_LLM_PROVIDER=openrouter
OPENROUTER_MODEL_NAME=meta-llama/llama-3.1-8b-instruct:free
```

**Free models available:**
- `meta-llama/llama-3.1-8b-instruct:free` (Good quality)
- `google/gemma-2-9b-it:free` (Fast)
- `mistralai/mistral-7b-instruct:free` (Balanced)

### Option 2: Hugging Face (Thousands of Models)

**Best for**: Experimenting with open-source models

1. Sign up: **https://huggingface.co/settings/tokens**
2. Create a read token (free)
3. Add to `.env`:

```bash
HUGGINGFACE_API_TOKEN=hf_your_token_here
DEFAULT_LLM_PROVIDER=huggingface
HF_MODEL_NAME=google/flan-t5-base
```

**Popular models:**
- `google/flan-t5-base` (Fast, good for testing)
- `meta-llama/Llama-2-7b-chat-hf` (Better quality)
- `mistralai/Mistral-7B-Instruct-v0.1` (Very capable)

### Option 3: OpenAI (Paid but Best Quality)

**Best for**: Production use, best responses

1. Sign up: **https://platform.openai.com/api-keys**
2. Add payment method (starts at $0.0005 per 1K tokens)
3. Create API key
4. Add to `.env`:

```bash
OPENAI_API_KEY=sk-your-key-here
DEFAULT_LLM_PROVIDER=openai
OPENAI_MODEL_NAME=gpt-4o-mini
```

**Cost**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens

---

## 📝 Complete .env Example

Create `backend/.env` with:

```bash
# Redis (optional - will use in-memory if not available)
REDIS_URL=redis://localhost:6379

# Choose ONE provider and add its API key:

# 1. Groq (Recommended - Free & Fast)
DEFAULT_LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL_NAME=llama-3.3-70b-versatile

# 2. OpenRouter (Alternative - Free tier)
# DEFAULT_LLM_PROVIDER=openrouter
# OPENROUTER_API_KEY=sk-or-v1-your-key-here
# OPENROUTER_MODEL_NAME=meta-llama/llama-3.1-8b-instruct:free

# 3. Hugging Face (Alternative - Free)
# DEFAULT_LLM_PROVIDER=huggingface
# HUGGINGFACE_API_TOKEN=hf_your_token_here
# HF_MODEL_NAME=google/flan-t5-base

# 4. OpenAI (Paid but best quality)
# DEFAULT_LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-key-here
# OPENAI_MODEL_NAME=gpt-4o-mini

# Gateway settings
API_KEYS=sk-nexus-dev-demo-key
SIMILARITY_THRESHOLD=0.92
```

---

## 🔍 How to Test Each Provider

### Testing in the UI

1. Go to http://localhost:8000
2. Select provider from dropdown:
   - **Groq** → Llama 3.3 70B
   - **OpenRouter** → Llama 3.1 8B (free)
   - **HuggingFace** → Flan-T5
   - **OpenAI** → GPT-4o-mini
   - **Mock** → Demo responses (no API key needed)

3. Enter any prompt and click "Execute Inference"

### Testing via API

```bash
curl -X POST http://localhost:8000/api/v1/infer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk-nexus-dev-demo-key" \
  -d '{
    "prompt": "What is Python?",
    "provider": "groq",
    "model": "llama-3.3-70b-versatile"
  }'
```

---

## 🎯 Provider Comparison

| Provider | Cost | Speed | Quality | Setup Time | Best For |
|----------|------|-------|---------|------------|----------|
| **Groq** | ✅ FREE | 🚀🚀🚀 | ⭐⭐⭐⭐⭐ | 2 min | Development & Production |
| **OpenRouter** | ✅ FREE tier | 🚀🚀 | ⭐⭐⭐⭐ | 2 min | Trying different models |
| **HuggingFace** | ✅ FREE | 🚀 | ⭐⭐⭐ | 3 min | Experimentation |
| **OpenAI** | 💰 PAID | 🚀🚀 | ⭐⭐⭐⭐⭐ | 5 min | Production apps |
| **Mock** | ✅ FREE | 🚀🚀🚀 | ⭐ | 0 min | Testing/Demo |

---

## 🚨 Troubleshooting

### "API key not configured" error

**Solution**: Make sure your `.env` file is in the `backend/` directory:
```bash
backend/.env  ← File must be here
backend/app/
```

### "Falling back to MockLLMProvider"

**Check**:
1. Is `GROQ_API_KEY` set in `backend/.env`?
2. Did you restart the server after adding the key?
3. Is the key correct? (Check for extra spaces)

### Provider returns error 401/403

**Solution**: Your API key is invalid or expired. Generate a new one from the provider's website.

### Groq returns "rate limit exceeded"

**Solution**: 
- Wait a minute (Groq has generous free limits)
- Or switch to OpenRouter free tier temporarily

---

## 💡 Tips

1. **Start with Groq** - It's free, fast, and high-quality
2. **Use semantic cache** - Reduces API calls by 70-90%
3. **Set provider in UI** - You can switch providers per request
4. **Monitor usage** - Check the Monitoring tab in the UI
5. **Production ready** - Groq is good enough for production use!

---

## 📚 More Resources

- **Groq Console**: https://console.groq.com
- **OpenRouter Models**: https://openrouter.ai/models
- **HuggingFace Hub**: https://huggingface.co/models
- **OpenAI Pricing**: https://openai.com/api/pricing

---

## ✅ Success Checklist

- [ ] Got API key from Groq (or another provider)
- [ ] Added key to `backend/.env`
- [ ] Set `DEFAULT_LLM_PROVIDER=groq`
- [ ] Restarted the server
- [ ] Tested a query in the UI
- [ ] Got real AI response (not mock)
- [ ] Saw "CACHE MISS" badge first time
- [ ] Saw "CACHE HIT" badge on repeat query

**Congratulations!** 🎉 You're now using real AI with semantic caching!
