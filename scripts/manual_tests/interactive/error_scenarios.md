# Error Scenarios Validation Checklist

**Purpose:** Manual validation of error handling and recovery in ragged.

**Estimated Time:** 30-40 minutes

**Last Updated:** 2025-11-19

---

## Prerequisites

- [ ] Ragged installed
- [ ] Ability to start/stop services (Ollama, ChromaDB)
- [ ] Test documents available
- [ ] Ability to simulate error conditions

---

## 1. Service Unavailability

### Test Case 1.1: Ollama Service Down

**Steps:**
1. Stop Ollama service
2. Try: `ragged query "test question"`
3. Restart Ollama
4. Retry query

**Expected Result:**
- Clear error: "Ollama service unavailable"
- Suggests checking Ollama is running
- Provides troubleshooting URL
- Recovers gracefully when service restored

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 1.2: ChromaDB Service Down

**Steps:**
1. Stop ChromaDB service
2. Try: `ragged add test.pdf`
3. Restart ChromaDB
4. Retry operation

**Expected Result:**
- Clear error: "ChromaDB unavailable"
- Explains impact
- Suggests troubleshooting
- Recovers when service restored

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 1.3: Both Services Down

**Steps:**
1. Stop both Ollama and ChromaDB
2. Try `ragged health`

**Expected Result:**
- Shows status of both services
- Clear indicators which are down
- Prioritised troubleshooting steps

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 2. Invalid Input Handling

### Test Case 2.1: Corrupted PDF

**Steps:**
1. Create corrupted PDF file
2. Try: `ragged add corrupted.pdf`

**Expected Result:**
- Error detected during processing
- Clear message: "File appears corrupted"
- Doesn't crash system
- Can continue with other files

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 2.2: Empty File

**Steps:**
1. Create empty file (0 bytes)
2. Try: `ragged add empty.txt`

**Expected Result:**
- Detects empty file
- Warns or skips gracefully
- Clear message to user

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 2.3: Extremely Large File

**Steps:**
1. Try to add very large file (>1GB)
2. Observe behaviour

**Expected Result:**
- Size limit warning (if applicable)
- Progress indicator for large files
- Graceful timeout handling
- Memory doesn't explode

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 2.4: Binary File as Text

**Steps:**
1. Try: `ragged add image.png` (if not supported)

**Expected Result:**
- Unsupported format error
- Lists supported formats
- Suggests alternatives

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 3. Configuration Errors

### Test Case 3.1: Invalid Config File

**Steps:**
1. Create malformed config file (invalid YAML/JSON)
2. Try to run ragged command

**Expected Result:**
- Config parsing error detected
- Shows line number of error
- Suggests fix
- Falls back to defaults if possible

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.2: Missing Config File

**Steps:**
1. Delete/rename config file
2. Run ragged command

**Expected Result:**
- Creates default config OR
- Uses sensible defaults
- Warns about missing config

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.3: Invalid Model Name

**Steps:**
1. `ragged config set-model --llm nonexistent_model`
2. Try query

**Expected Result:**
- Validation error
- Lists available models
- Prevents invalid configuration

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 4. Resource Exhaustion

### Test Case 4.1: Disk Full

**Steps:**
1. Fill disk to near capacity
2. Try to add documents

**Expected Result:**
- Disk space error detected
- Clear message about low space
- Doesn't corrupt database
- Graceful failure

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 4.2: Memory Exhaustion

**Steps:**
1. Try to process many large documents simultaneously
2. Monitor memory usage

**Expected Result:**
- Memory limits respected
- Graceful degradation
- Progress not lost
- Clear error if OOM

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 4.3: Too Many Open Files

**Steps:**
1. Ingest large number of files
2. Check file descriptor usage

**Expected Result:**
- Files closed properly
- No file descriptor leaks
- Batch processing if needed

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 5. Network Issues

### Test Case 5.1: Slow Connection

**Steps:**
1. Simulate slow network
2. Try operations requiring network

**Expected Result:**
- Appropriate timeouts
- Progress indicators
- Doesn't hang indefinitely
- Retry capability

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 5.2: Connection Reset

**Steps:**
1. Start operation
2. Reset network connection mid-operation
3. Restore connection

**Expected Result:**
- Error detected
- Operation can be retried
- Data not corrupted
- Clear error message

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 6. Permission Errors

### Test Case 6.1: No Write Permission

**Steps:**
1. Make data directory read-only
2. Try to add document

**Expected Result:**
- Permission error detected
- Clear message about permissions
- Suggests fix (chmod, etc.)

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 6.2: No Read Permission

**Steps:**
1. Make file unreadable
2. Try: `ragged add unreadable_file.pdf`

**Expected Result:**
- Read permission error
- Clear message
- Skips file if batch operation

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 7. Concurrent Operations

### Test Case 7.1: Simultaneous Writes

**Steps:**
1. Start document ingestion in terminal 1
2. Start another ingestion in terminal 2

**Expected Result:**
- Operations complete without conflict
- Database locking works correctly
- No data corruption

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 7.2: Read During Write

**Steps:**
1. Start large ingestion
2. Query while ingesting

**Expected Result:**
- Query works (reads existing data)
- No blocking or deadlock
- Performance acceptable

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 8. Edge Cases

### Test Case 8.1: Unicode Handling

**Steps:**
1. Add document with Unicode filename and content (中文, emoji, etc.)
2. Query for Unicode content

**Expected Result:**
- Unicode handled correctly
- No encoding errors
- Searchable and retrievable

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 8.2: Very Long Query

**Steps:**
1. Submit extremely long query (>10,000 characters)

**Expected Result:**
- Query length validation
- Truncation warning if needed
- Graceful handling

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 8.3: Special Characters in Filenames

**Steps:**
1. Add files with special characters: `file with spaces.pdf`, `file's.pdf`, `file#1.pdf`

**Expected Result:**
- All filenames handled
- Proper escaping
- Retrievable by name

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 9. Recovery Scenarios

### Test Case 9.1: Interrupt During Ingestion

**Steps:**
1. Start ingestion
2. Press Ctrl+C mid-way
3. Try to ingest again

**Expected Result:**
- Graceful shutdown
- Database remains consistent
- Can resume/retry

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 9.2: Crash Recovery

**Steps:**
1. Kill ragged process during operation
2. Restart and check state

**Expected Result:**
- Database not corrupted
- Partial operations handled
- State recoverable

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 10. Graceful Degradation

### Test Case 10.1: Limited Resources

**Steps:**
1. Run on resource-constrained system
2. Observe behaviour

**Expected Result:**
- Adapts to available resources
- Slower but still functional
- Clear feedback on limitations

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 10.2: Partial Service Availability

**Steps:**
1. Run with only basic features available
2. Test fallback behaviour

**Expected Result:**
- Core functionality works
- Optional features disabled gracefully
- Clear indication of what's unavailable

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## Summary

**Total Test Cases:** 26
**Passed:** ____
**Failed:** ____
**N/A:** ____

**Pass Rate:** ____%

---

## Critical Issues Found

| Issue # | Scenario | Impact | Severity |
|---------|----------|--------|----------|
| 1 | | | ☐ Critical ☐ High ☐ Medium ☐ Low |
| 2 | | | ☐ Critical ☐ High ☐ Medium ☐ Low |

---

## Error Handling Quality Assessment

**Error Messages:**
- [ ] Clear and actionable
- [ ] Include context
- [ ] Suggest solutions
- [ ] Appropriate severity

**Recovery:**
- [ ] Graceful failure
- [ ] Data integrity maintained
- [ ] Operations can be retried
- [ ] System remains stable

**User Experience:**
- [ ] Not overwhelming
- [ ] Professional tone
- [ ] Helpful guidance
- [ ] Appropriate detail level

---

**Tested By:** ____________________
**Date:** ____________________
**ragged Version:** ____________________

---

**Maintained By:** ragged development team
