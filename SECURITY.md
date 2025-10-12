# Security Policy

## Supported Versions

The following table shows which versions of Ouroboros are currently being supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.12.x  | :white_check_mark: |
| < 1.12  | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Ouroboros, please help us by reporting it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please use one of the following methods:

1. **GitHub Security Advisories** (Preferred)

   - Go to the [Security tab](https://github.com/UncleSp1d3r/Ouroboros/security) of this repository
   - Click "Report a vulnerability"
   - Fill out the security advisory form

2. **Private Email** (Alternative)

   - Email: [UncleSp1d3r](mailto:unclespider@protonmail.com)
   - Subject: "Ouroboros Security Report"
   - Include detailed information about the vulnerability
   - My PGP key is available [on keys.openpgp.org](https://keys.openpgp.org/vks/v1/by-fingerprint/6F21D117858E4C8F7BE79DCFDEB64E8A0CA4ED3Ee)

### What to Include

When reporting a vulnerability, please include as much of the following information as possible:

- **Type of vulnerability** (e.g., SQL injection, cross-site scripting, authentication bypass)
- **Affected component(s)** (e.g., web interface, API endpoints, agent communication)
- **Step-by-step reproduction instructions**
- **Proof of concept or exploit code** (if available)
- **Potential impact** of the vulnerability
- **Suggested fix** (if you have one)

### Response Timeline

As a single maintainer, I aim for the following response times:

- **Initial Response**: Within 1 week of report submission
- **Vulnerability Assessment**: Within 2 weeks
- **Fix Development**: Varies based on complexity and my availability (typically 1-6 weeks)
- **Public Disclosure**: After fix is released and tested

**Note**: I have a day job, so responses may be slower during busy periods.

### What I Can Handle

**I can investigate and fix:**

- Code vulnerabilities in the Ouroboros codebase
- Configuration security issues
- Dependency vulnerabilities (via `uv`)

**I cannot handle:**

- Infrastructure security (deployment-specific)
- Network-level attacks
- Third-party service vulnerabilities
- Zero-day exploits in dependencies (I'll update when patches are available)

### What to Expect

- **Acknowledgments**: I'll confirm receipt and keep you updated
- **Timeline**: Realistic estimates based on my availability
- **Credit**: I'll acknowledge you in the advisory (if you want)
- **No monetary rewards**: This is a hobby project

**What I ask:**

- Be patient - I'm one person with limited time
- Provide clear reproduction steps
- Don't expect enterprise-level response times

### Security Update Process

1. **Acknowledgment**: We'll confirm receipt of your report
2. **Investigation**: We'll investigate and validate the vulnerability
3. **Fix Development**: We'll develop and test a fix
4. **Release**: We'll release a security update
5. **Disclosure**: We'll publish a security advisory with details

## Security Best Practices for Users

### For Operators

- **Keep Ouroboros Updated**: Always use the latest supported version
- **Network Security**: Deploy behind proper firewall rules and network segmentation
- **Access Control**: Use strong authentication and limit user privileges
- **Monitoring**: Monitor logs for suspicious activities
- **Backup Strategy**: Maintain secure backups of your data

### For Developers/Contributors

- **Secure Development**: Follow secure coding practices
- **Dependency Management**: Keep dependencies updated using `uv` and monitor for vulnerabilities
- **Testing**: Run security tests before contributing (`just ci-check`)
- **Code Review**: All changes go through pull request review process

## Known Security Considerations

### Agent Communication

- All agent communications use authenticated API endpoints
- API keys should be rotated regularly
- Use HTTPS in production deployments

### Password Handling

- Ouroboros handles password hashes, never plaintext passwords
- Ensure proper access controls on hash list uploads
- Use appropriate network security when handling sensitive data

### Web Interface

- Session management uses secure HTTP-only cookies
- CSRF protection is enabled for all state-changing operations
- Input validation is enforced via Pydantic schemas

## Security Tools and Automation

This project uses several automated security measures:

- **Dependency Scanning**: Automated dependency vulnerability scanning
- **Code Analysis**: Static analysis via pre-commit hooks
- **Container Scanning**: Docker image vulnerability scanning in CI/CD
- **Secret Detection**: Automated secret detection in commits

## Security Reality Check

This is a password cracking tool - by nature it handles sensitive data. Users should:

- Deploy in isolated environments
- Use strong access controls
- Monitor for abuse
- Understand the risks of running security tools

I focus on fixing code vulnerabilities, but users are responsible for their deployment security.

## Contact

For non-security related issues, please use the [GitHub Issues](https://github.com/UncleSp1d3r/Ouroboros/issues) page.

For questions about this security policy, you can:

- Create a [GitHub Discussion](https://github.com/UncleSp1d3r/Ouroboros/discussions)
- Open a general [GitHub Issue](https://github.com/UncleSp1d3r/Ouroboros/issues)

## Acknowledgments

We appreciate the security research community's efforts in responsibly disclosing vulnerabilities. Contributors who report valid security issues will be acknowledged in our security advisories (with their permission).

---

**Note**: This is an open-source password cracking platform. While we take security seriously, users should understand the inherent risks of deploying security testing tools and take appropriate precautions for their specific use cases.
