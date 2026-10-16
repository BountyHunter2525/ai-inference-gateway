# Contributing to NexusAI

Thanks for considering contributing to NexusAI! This is a college project, but improvements and bug fixes are welcome.

---

## 🤝 How to Contribute

### Reporting Bugs

Found a bug? Please open an issue with:
- Description of the bug
- Steps to reproduce
- Expected vs actual behavior
- System info (OS, Python version)
- Error logs if available

### Suggesting Features

Have an idea? Open an issue with:
- Clear description of the feature
- Why it would be useful
- How it might work

### Code Contributions

Want to contribute code? Great!

**Steps:**

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/ai-inference-gateway.git
   cd ai-inference-gateway
   ```

3. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

4. **Make your changes**
   - Write clear, commented code
   - Follow existing code style
   - Add tests if applicable

5. **Test your changes**
   ```bash
   cd backend
   pytest -v
   ```

6. **Commit with clear message**
   ```bash
   git commit -m "feat: add cool new feature"
   # or
   git commit -m "fix: resolve cache eviction bug"
   ```

7. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Then open Pull Request on GitHub
   ```

---

## 📝 Commit Message Format

Use conventional commits:

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation only
- `style:` — Code formatting (no logic change)
- `refactor:` — Code restructure (no feature/bug change)
- `test:` — Adding tests
- `chore:` — Maintenance tasks

**Examples:**
```
feat: add response streaming with SSE
fix: resolve Redis connection timeout
docs: update deployment guide for Railway
test: add unit tests for TTL policy
```

---

## 🎨 Code Style

### Python
- Follow PEP 8
- Use type hints
- Add docstrings for functions
- Keep functions small and focused
- Use meaningful variable names

**Example:**
```python
def calculate_similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Similarity score between 0 and 1
    """
    return np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )
```

### JavaScript
- Use const/let (not var)
- Use async/await (not callbacks)
- Add comments for complex logic
- Keep functions small

### General
- Indent with 4 spaces (Python) or 2 spaces (JS)
- One feature per commit
- Test before committing
- Update docs if needed

---

## 🧪 Testing

All new features should include tests.

**Run tests:**
```bash
cd backend
pytest -v
```

**Run specific test:**
```bash
pytest tests/test_cache.py::test_similarity_matching -v
```

**Check coverage:**
```bash
pytest --cov=app --cov-report=html
```

---

## 📚 Documentation

If you change functionality, update:
- README.md (if user-facing)
- USAGE_GUIDE.md (if API changes)
- Docstrings in code
- Type hints

---

## 🚫 What NOT to Contribute

- Large code rewrites without discussion
- New dependencies without justification
- Breaking changes to public API
- Code without tests
- Features that don't fit the project scope

**Always open an issue first to discuss major changes!**

---

## 🎯 Good First Issues

New to the project? Try these:

- Fix typos in documentation
- Add more unit tests
- Improve error messages
- Add code comments
- Update .env.example with new fields

---

## 🐛 Bug Fix Process

1. **Reproduce** — Confirm the bug exists
2. **Test** — Write a failing test
3. **Fix** — Make it pass
4. **Verify** — Run all tests
5. **Document** — Add to changelog if needed

---

## ✨ Feature Development Process

1. **Discuss** — Open issue to discuss approach
2. **Design** — Plan the implementation
3. **Implement** — Write the code
4. **Test** — Add comprehensive tests
5. **Document** — Update relevant docs
6. **Review** — Submit PR for review

---

## 📋 Pull Request Checklist

Before submitting:

- [ ] Code follows project style
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages are clear
- [ ] No breaking changes (or discussed first)
- [ ] Branch is up to date with main

---

## 🔍 Code Review Process

After submitting your PR:

1. **Automated checks** run (tests, lint)
2. **Maintainer review** (may take a few days)
3. **Feedback** addressed (if any)
4. **Approval & merge**

Be patient and responsive to feedback!

---

## 💬 Communication

- **Issues** — For bugs and features
- **Discussions** — For questions and ideas
- **PRs** — For code contributions

Be respectful and constructive. Everyone's learning!

---

## 🎓 Learning Opportunity

This is a college project, so contributions are a great learning opportunity:

- Practice Git workflow
- Learn code review process
- Understand FastAPI/Python/ML
- Collaborate with others
- Build your portfolio

---

## 📜 Code of Conduct

Be kind and respectful:
- ✅ Welcome newcomers
- ✅ Provide constructive feedback
- ✅ Assume good intentions
- ✅ Be patient with questions

---

## 🙏 Thank You!

Every contribution helps:
- Bug reports improve quality
- Feature suggestions guide development
- Code contributions add functionality
- Documentation helps everyone

**Thank you for making NexusAI better! 🚀**

---

## 📞 Questions?

Not sure about something? Feel free to:
- Open an issue with your question
- Ask in a discussion thread
- Comment on relevant issues

**No question is too small!**
