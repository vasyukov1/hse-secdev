# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Security Measures

### Input Validation
- All API inputs validated with Pydantic schemas
- Custom URL validation with security checks
- Request size limits (1MB maximum)

### Error Handling
- RFC 7807 compliant error responses
- Correlation IDs for error tracing
- No sensitive data exposure in errors

### Data Protection
- Parameterized SQL queries via SQLAlchemy
- No raw SQL queries in code
- Secure database connection handling

### API Security
- Request rate limiting (via infrastructure)
- Input sanitization and validation
- Secure error messages

## Reporting a Vulnerability

To report a security vulnerability, please create a GitHub issue with the "security" label.

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Security Updates

Security-related updates will be released as patch versions (0.3.x) and documented in:
- Release notes
- ADR documents in `docs/adr/`
- Security bulletins in issues
