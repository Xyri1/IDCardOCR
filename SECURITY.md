# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of IDCardOCR seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please Do Not

- Open a public GitHub issue for security vulnerabilities
- Disclose the vulnerability publicly before it has been addressed

### Please Do

1. **Email** the maintainers privately (if you have contact info)
2. **Open a private security advisory** on GitHub (if available)
3. Provide detailed information about the vulnerability:
   - Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
   - Full paths of source file(s) related to the manifestation of the issue
   - The location of the affected source code (tag/branch/commit or direct URL)
   - Any special configuration required to reproduce the issue
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment**: Within 48 hours of your report
- **Updates**: Regular updates on the progress of fixing the vulnerability
- **Credit**: Recognition in the security advisory (if you wish)
- **Fix timeline**: We aim to patch critical vulnerabilities within 7 days

## Security Best Practices

### For Users

1. **Protect Your Credentials**
   - Never commit `.env` file to version control
   - Never share your Tencent Cloud API credentials
   - Use separate credentials for development and production
   - Rotate credentials regularly

2. **Data Protection**
   - Ensure you have authorization to process ID card data
   - Store extracted data securely
   - Implement access controls for generated files
   - Comply with GDPR, CCPA, and other data protection regulations
   - Delete data when no longer needed

3. **Secure Configuration**
   - Keep Python and dependencies up to date
   - Use virtual environments
   - Review dependency security advisories
   - Enable rate limiting to prevent abuse

4. **Network Security**
   - Use HTTPS for all API communications (default)
   - Consider using VPN for sensitive operations
   - Monitor API access logs
   - Implement IP whitelist if possible

### For Developers

1. **Code Security**
   - Sanitize all inputs
   - Validate API responses
   - Use parameterized queries if adding database support
   - Avoid hardcoding credentials
   - Use secure random generation for sensitive operations

2. **Dependency Management**
   - Keep dependencies updated
   - Run security audits: `pip-audit` or `safety check`
   - Review dependency licenses
   - Pin dependency versions

3. **Testing**
   - Never use production credentials in tests
   - Don't include real ID card data in test suites
   - Use mock data for sensitive operations
   - Test with edge cases and invalid inputs

4. **Code Review**
   - Review all PRs for security implications
   - Check for credential leaks
   - Verify input validation
   - Ensure proper error handling

## Known Security Considerations

### Data Privacy

This application processes **sensitive personal information** including:
- Full names
- ID numbers
- Addresses
- Dates of birth
- Photos

Users MUST:
- Have legal authorization to process this data
- Implement appropriate security measures
- Comply with data protection regulations
- Inform data subjects as required by law

### API Security

- **Rate Limiting**: Built-in (20 req/s) but can be increased
- **Credentials**: Stored in `.env` (not committed to git)
- **Data Transmission**: HTTPS only (Tencent Cloud default)
- **Data Storage**: Files stored locally - secure your system

### Logging

The application logs:
- Processing statistics
- API errors
- File operations

Logs DO NOT include:
- API credentials
- Full ID card numbers
- Personal addresses

However, logs may contain:
- Filenames (which may contain names)
- Processing status

Secure your log files appropriately.

## Compliance

### GDPR (EU)

If processing EU residents' data:
- Obtain explicit consent
- Implement data minimization
- Provide data access/deletion mechanisms
- Maintain processing records
- Implement appropriate technical measures

### CCPA (California)

If processing California residents' data:
- Inform users about data collection
- Provide opt-out mechanisms
- Honor deletion requests
- Maintain data security

### Other Regulations

Check your local data protection laws and ensure compliance.

## Security Updates

Security updates will be:
- Announced in GitHub releases
- Tagged with `security` label
- Documented in CHANGELOG
- Include upgrade instructions

Subscribe to repository notifications to stay informed.

## Additional Resources

- [OWASP Top Ten](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Tencent Cloud Security Best Practices](https://cloud.tencent.com/document/product/301/11281)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

**Last Updated**: November 2025

Thank you for helping keep IDCardOCR and its users safe!

