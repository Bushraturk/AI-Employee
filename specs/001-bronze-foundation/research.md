# Research: Bronze Phase - Local Foundation

**Feature**: 001-bronze-foundation
**Date**: 2026-02-14
**Phase**: Phase 0 - Research & Technology Decisions

## Overview

This document captures research findings and technology decisions for the Bronze phase implementation. All decisions prioritize local-first operation, simplicity, and alignment with constitution principles.

---

## Decision 1: File Watching Library

**Question**: How should the system monitor the Inbox folder for new files?

**Options Considered**:

1. **watchdog** (Python library)
   - Cross-platform (Windows, macOS, Linux)
   - Event-driven (immediate detection)
   - Mature and well-maintained
   - Supports recursive watching
   - ~2.0MB memory footprint

2. **Polling with os.listdir()**
   - Simple implementation
   - No external dependencies
   - Higher latency (polling interval)
   - More CPU usage
   - Harder to detect file modifications

3. **inotify (Linux), FSEvents (macOS), ReadDirectoryChangesW (Windows)**
   - Platform-specific APIs
   - Lowest latency
   - Requires platform-specific code
   - Complex implementation

**Decision**: **watchdog**

**Rationale**:
- Meets 2-second detection requirement with event-driven architecture
- Cross-platform support aligns with constitution's platform requirements
- Mature library reduces implementation risk
- Event-driven approach is more efficient than polling
- Well-documented and actively maintained

**Alternatives Rejected**:
- Polling: Too high latency and CPU usage for 2-second requirement
- Platform-specific APIs: Violates cross-platform requirement, increases complexity

---

## Decision 2: Markdown Parsing

**Question**: How should the system parse Markdown task files with YAML frontmatter?

**Options Considered**:

1. **python-frontmatter + markdown**
   - Dedicated frontmatter parsing
   - Separates metadata from content
   - Handles YAML parsing automatically
   - ~500KB combined size

2. **PyYAML + regex splitting**
   - Manual frontmatter extraction
   - More control over parsing
   - Requires custom delimiter detection
   - Error-prone edge cases

3. **markdown-it-py**
   - Full Markdown parser
   - No built-in frontmatter support
   - Overkill for simple parsing

**Decision**: **python-frontmatter + markdown**

**Rationale**:
- Purpose-built for YAML frontmatter extraction
- Handles edge cases (missing frontmatter, malformed YAML)
- Clean separation of metadata and content
- Minimal dependencies
- Widely used in static site generators (proven pattern)

**Alternatives Rejected**:
- Manual parsing: Too error-prone, reinventing the wheel
- markdown-it-py: Doesn't solve frontmatter problem, adds complexity

---

## Decision 3: Claude Code Integration

**Question**: How should the system invoke Claude Code for task processing?

**Options Considered**:

1. **subprocess with JSON I/O**
   - Invoke Claude Code CLI as subprocess
   - Pass task data via stdin (JSON)
   - Receive response via stdout (JSON)
   - Standard Python library (no dependencies)

2. **Claude API (Anthropic SDK)**
   - Direct API calls
   - Requires API key and internet
   - Violates local-first principle
   - Monthly costs

3. **File-based communication**
   - Write task to temp file
   - Invoke Claude Code with file path
   - Read response from output file
   - More I/O overhead

**Decision**: **subprocess with JSON I/O**

**Rationale**:
- Maintains local-first architecture (Claude Code CLI runs locally)
- No external dependencies beyond Claude Code CLI
- Standard Python subprocess module
- Clean JSON interface for structured data
- Aligns with constitution's local-first principle

**Alternatives Rejected**:
- Claude API: Violates local-first requirement, requires internet
- File-based: Unnecessary I/O overhead, temp file cleanup complexity

---

## Decision 4: Concurrency Model

**Question**: Should the system use async/await or synchronous threading?

**Options Considered**:

1. **Synchronous with threading**
   - Simple mental model
   - Standard library (threading module)
   - Sequential task processing
   - Easier debugging
   - Sufficient for Bronze phase (100 tasks/day)

2. **asyncio with async/await**
   - Better for high concurrency
   - More complex error handling
   - Requires async-compatible libraries
   - Overkill for Bronze phase scale

3. **multiprocessing**
   - True parallelism
   - Higher memory overhead
   - Complex inter-process communication
   - Unnecessary for I/O-bound workload

**Decision**: **Synchronous with threading**

**Rationale**:
- Bronze phase processes tasks sequentially (no parallel requirement)
- Simpler implementation reduces bugs
- Easier to reason about state and logging
- Threading sufficient for file watching + task processing
- Can migrate to asyncio in Gold phase if needed

**Alternatives Rejected**:
- asyncio: Premature optimization, adds complexity
- multiprocessing: Overkill for I/O-bound workload, memory overhead

---

## Decision 5: Configuration Management

**Question**: How should the system handle configuration (vault path, polling intervals)?

**Options Considered**:

1. **Environment variables + .env file**
   - Standard approach (12-factor app)
   - python-dotenv library
   - Easy to override per environment
   - No config file parsing needed

2. **YAML/JSON config file**
   - Structured configuration
   - Requires file parsing
   - More complex validation
   - Harder to override

3. **Command-line arguments only**
   - Simple implementation
   - Tedious for multiple settings
   - No persistent configuration
   - Poor user experience

**Decision**: **Environment variables + .env file**

**Rationale**:
- Industry standard (12-factor app methodology)
- Easy to override for testing
- python-dotenv is lightweight and mature
- Supports secrets management (future phases)
- Simple validation with os.getenv() defaults

**Alternatives Rejected**:
- Config file: Adds parsing complexity, harder to override
- CLI args only: Poor UX for persistent settings

---

## Decision 6: Error Handling Strategy

**Question**: How should the system handle errors during task processing?

**Options Considered**:

1. **Try-catch with logging + task retry**
   - Catch exceptions at each stage
   - Log error details
   - Move failed tasks to separate folder
   - Retry with exponential backoff

2. **Fail fast (crash on error)**
   - Simple implementation
   - Requires manual restart
   - Loses in-flight tasks
   - Poor production readiness

3. **Error tasks stay in Needs_Action**
   - Failed tasks remain visible
   - Manual intervention required
   - No automatic retry
   - Simple but less autonomous

**Decision**: **Try-catch with logging + task retry**

**Rationale**:
- Aligns with constitution's graceful error handling requirement
- Maintains system uptime (24-hour operation requirement)
- Provides visibility through logs
- Exponential backoff prevents infinite loops
- Production-ready approach

**Alternatives Rejected**:
- Fail fast: Violates 24-hour uptime requirement
- No retry: Less autonomous, requires manual intervention

---

## Decision 7: Dashboard Update Strategy

**Question**: How should Dashboard.md be updated to ensure atomicity?

**Options Considered**:

1. **Write to temp file + atomic rename**
   - Write new content to Dashboard.tmp
   - Use os.replace() for atomic rename
   - Prevents partial reads
   - Standard atomic file update pattern

2. **Direct file write**
   - Simple implementation
   - Risk of partial reads during write
   - Not atomic on all filesystems
   - Violates constitution's atomic requirement

3. **File locking**
   - Lock file during write
   - Complex cross-platform implementation
   - Potential deadlocks
   - Overkill for single-writer scenario

**Decision**: **Write to temp file + atomic rename**

**Rationale**:
- Guarantees atomic updates (constitution requirement)
- Prevents users from seeing partial dashboard state
- Standard pattern for atomic file updates
- Cross-platform support via os.replace()
- Simple implementation

**Alternatives Rejected**:
- Direct write: Not atomic, violates constitution
- File locking: Unnecessary complexity for single writer

---

## Decision 8: Logging Format

**Question**: What format should audit logs use?

**Options Considered**:

1. **Markdown with structured sections**
   - Human-readable
   - Aligns with "Markdown as memory" principle
   - Easy to grep/search
   - Consistent with vault format

2. **JSON Lines (JSONL)**
   - Machine-parseable
   - Structured data
   - Harder for humans to read
   - Requires parsing for viewing

3. **Plain text**
   - Simplest format
   - No structure
   - Hard to parse programmatically
   - Limited metadata

**Decision**: **Markdown with structured sections**

**Rationale**:
- Aligns with constitution's "Markdown as system memory" principle
- Human-readable for debugging
- Structured enough for programmatic parsing
- Consistent with vault format (Dashboard.md, tasks)
- Easy to view in Obsidian

**Alternatives Rejected**:
- JSONL: Violates Markdown principle, harder for humans
- Plain text: Insufficient structure for audit requirements

---

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Language | Python | 3.11 (min 3.9) | Type hints, asyncio support, cross-platform |
| File Watching | watchdog | 3.0+ | Event-driven, cross-platform, mature |
| Markdown Parsing | python-frontmatter | 1.0+ | YAML frontmatter extraction |
| Markdown Rendering | markdown | 3.4+ | Content parsing (if needed) |
| Configuration | python-dotenv | 1.0+ | Environment variable management |
| Testing | pytest | 7.4+ | Standard Python testing framework |
| Async Testing | pytest-asyncio | 0.21+ | Async test support (future phases) |
| Test Timeouts | pytest-timeout | 2.1+ | Prevent hanging tests |
| Claude Integration | subprocess | stdlib | Local CLI invocation |
| Path Operations | pathlib | stdlib | Modern path handling |
| Logging | logging | stdlib | Standard Python logging |

---

## Performance Considerations

### File Detection Latency

- watchdog event-driven architecture: <100ms typical latency
- Meets 2-second requirement with 20x margin
- No polling overhead

### Memory Usage

- Python interpreter: ~50MB base
- watchdog: ~2MB
- Task processing: ~10MB per task (estimated)
- Dashboard/logs: <1MB
- **Total estimated**: ~100MB typical, <500MB under load ✅

### Task Processing Throughput

- Sequential processing: 1 task at a time
- 30-second average processing time
- Theoretical max: 2,880 tasks/day (24h × 60min × 2 tasks/hour)
- Target: 100 tasks/day (3.5% utilization) ✅

---

## Security Considerations

### Path Validation

- All file operations validate paths are within vault
- Use pathlib.resolve() to prevent directory traversal
- Reject symlinks outside vault

### Command Injection

- subprocess with list args (not shell=True)
- No user input passed to shell
- JSON serialization prevents injection

### Secrets Management

- .env file for configuration (not committed to git)
- No hardcoded paths or credentials
- Environment variables for sensitive data

---

## Next Steps

Phase 1 artifacts to create:
1. data-model.md - Entity definitions
2. contracts/task-schema.yaml - Task file format
3. quickstart.md - Setup instructions
