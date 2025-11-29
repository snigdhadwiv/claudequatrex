# Contributing to Real-Time Voice Assistant

Thank you for your interest in contributing! This document provides guidelines for contributing to
the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/real-time-voice-assistant.git`
3. Create a virtual environment: `python -m venv venv`
4. Install dependencies: `pip install -r requirements.txt`
5. Install dev dependencies: `pip install pytest black flake8`

## Development Workflow

### Creating a Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:

- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

### Making Changes

1. Make your changes
2. Write/update tests
3. Run tests: `pytest tests/`
4. Format code: `black src/ tests/`
5. Check style: `flake8 src/ tests/`

### Committing

Write clear, descriptive commit messages:

```
Add streaming support to TTS engine

- Implement sentence-level synthesis
- Add audio chunk generator
- Update tests for streaming mode
- Document new parameters
```

### Testing

- Write unit tests for new functionality
- Ensure all tests pass
- Aim for >80% code coverage
- Test on multiple platforms if possible

### Documentation

- Update relevant documentation
- Add docstrings to new functions/classes
- Update README if needed
- Add usage examples

## Code Style

### Python Style Guide

Follow PEP 8 with these specifications:

- Line length: 100 characters
- Use type hints
- Write docstrings (Google style)
- Use meaningful variable names

Example:

```python
def process_audio(
    audio_data: np.ndarray,
    sample_rate: int = 16000,
    normalize: bool = True
) -> np.ndarray:
    """
    Process audio data with optional normalization.
    
    Args:
        audio_data: Input audio as numpy array
        sample_rate: Sample rate in Hz
        normalize: Whether to normalize audio
        
    Returns:
        Processed audio data
        
    Raises:
        ValueError: If audio_data is empty
    """
    if len(audio_data) == 0:
        raise ValueError("Empty audio data")
    
    # Processing logic here
    return processed_audio
```

### Documentation Style

- Use Markdown for documentation
- Include code examples
- Add diagrams where helpful
- Keep it clear and concise

## Pull Request Process

### Before Submitting

- [ ] All tests pass
- [ ] Code is formatted (black)
- [ ] No linting errors (flake8)
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### Submitting

1. Push to your fork: `git push origin feature/your-feature-name`
2. Create Pull Request on GitHub
3. Fill out PR template
4. Link related issues

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Areas for Contribution

### High Priority

- Performance optimizations
- Additional language support
- Mobile platform support
- Cloud integration options
- Advanced NLP models

### Medium Priority

- UI/Web interface
- Voice cloning features
- Emotion recognition
- Additional TTS engines
- Improved error handling

### Documentation

- Tutorial videos
- Usage examples
- Architecture diagrams
- API documentation
- Translation to other languages

### Testing

- Integration tests
- Performance benchmarks
- Edge case testing
- Cross-platform testing

## Reporting Issues

### Bug Reports

Include:

- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- System information (OS, Python version)
- Logs/error messages
- Screenshots if applicable

### Feature Requests

Include:

- Problem description
- Proposed solution
- Use case examples
- Alternative solutions considered

## Community Guidelines

### Be Respectful

- Be kind and courteous
- Respect different viewpoints
- Accept constructive criticism
- Focus on what's best for the project

### Be Collaborative

- Help others learn
- Share knowledge
- Review others' PRs
- Participate in discussions

### Be Professional

- Use appropriate language
- Stay on topic
- Provide constructive feedback
- Credit others' work

## Questions?

- Open an issue for general questions
- Join our community chat
- Email maintainers for sensitive issues

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Acknowledged in release notes
- Invited to maintainer team (for significant contributions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
