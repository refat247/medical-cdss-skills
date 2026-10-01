# Keep a Changelog Specification & Standard Conventions

This reference defines changelog formatting standards based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## 1. Guiding Principles

1. **Changelogs are for humans, not machines.** Write clear, high-signal explanations rather than raw git commit hashes.
2. **One entry per change.** Group related items under the appropriate release header.
3. **Reverse chronological order.** The latest release must always be at the top of the file.
4. **Standardized ISO dates.** Always format release dates as `YYYY-MM-DD`.
5. **SemVer link.** Each version heading must correspond directly to a valid Semantic Version.

---

## 2. Standard Changelog Template

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Feature description for work not yet published in an official release.

## [1.1.0] - 2026-09-15

### Added
- New feature A with optional configuration flag.
- New unit test coverage for feature A.

### Changed
- Refactored internal parsing pipeline to reduce memory footprint.

### Fixed
- Fixed regex edge case when parsing multiline strings.

## [1.0.0] - 2026-09-14

### Added
- Initial production release.
- Core engine and test suite.
```

---

## 3. Standard Change Categories

Always categorize release items under one of the six standard types:

- **`Added`**: For new features, flags, capabilities, or test suites.
- **`Changed`**: For changes in existing functionality, refactoring, or performance improvements.
- **`Deprecated`**: For soon-to-be removed features (to give downstream consumers warning).
- **`Removed`**: For features, flags, or endpoints removed in this release.
- **`Fixed`**: For any bug fixes, patch repairs, or error handler corrections.
- **`Security`**: For vulnerability remediations, security patches, or credential handling improvements.

---

## 4. Prepending New Releases

When releasing a new version:
1. Insert the new release section directly below the header or `[Unreleased]` section.
2. Format header: `## [X.Y.Z] - YYYY-MM-DD`.
3. Include relevant categories (`Added`, `Changed`, `Fixed`, etc.).
4. If an `[Unreleased]` section was tracking changes, move those changes into the new release header and clear `[Unreleased]`.
