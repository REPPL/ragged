# CLI Features Validation Checklist

**Purpose:** Manual verification of ragged CLI command functionality and user experience.

**Estimated Time:** 20-30 minutes

**Last Updated:** 2025-11-19

---

## Prerequisites

- [ ] Ragged installed and in PATH
- [ ] Ollama service running
- [ ] ChromaDB service running
- [ ] Test documents available

---

## 1. Core Commands

### Test Case 1.1: `ragged add` - Single File

**Steps:**
```bash
ragged add test_document.pdf
```

**Expected Result:**
- File ingests successfully
- Progress indicator shown
- Success message displayed
- Document ID returned

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 1.2: `ragged add` - Multiple Files

**Steps:**
```bash
ragged add file1.pdf file2.md file3.txt
```

**Expected Result:**
- All files ingest
- Progress for each file
- Summary of results

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 1.3: `ragged add` - Folder

**Steps:**
```bash
ragged add /path/to/folder --recursive
```

**Expected Result:**
- Recursive scan works
- All files processed
- Duplicates detected
- Summary provided

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 1.4: `ragged query`

**Steps:**
```bash
ragged query "What is retrieval-augmented generation?"
```

**Expected Result:**
- Query executes
- Response displayed
- Sources shown
- Response time reasonable

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 1.5: `ragged list`

**Steps:**
```bash
ragged list
```

**Expected Result:**
- All documents listed
- Metadata shown (name, date, size)
- Formatted readably
- Accurate count

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 1.6: `ragged clear`

**Steps:**
```bash
ragged clear
# Confirm deletion
```

**Expected Result:**
- Confirmation prompt
- All documents deleted
- Database cleared
- Success message

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 2. Output Formatting (v0.2.8+)

### Test Case 2.1: JSON Output

**Steps:**
```bash
ragged list --format json
ragged query "test" --format json
```

**Expected Result:**
- Valid JSON output
- Properly structured
- Parseable
- All data included

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 2.2: Table Output

**Steps:**
```bash
ragged list --format table
```

**Expected Result:**
- Formatted table
- Aligned columns
- Headers clear
- Readable layout

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 2.3: CSV Output

**Steps:**
```bash
ragged list --format csv > output.csv
```

**Expected Result:**
- Valid CSV format
- Proper escaping
- Headers included
- Importable in spreadsheet

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 2.4: YAML Output

**Steps:**
```bash
ragged list --format yaml
```

**Expected Result:**
- Valid YAML
- Proper indentation
- Readable structure
- Parseable

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 3. Advanced Commands (v0.2.8+)

### Test Case 3.1: `ragged metadata`

**Steps:**
```bash
ragged metadata list
ragged metadata show <doc_id>
ragged metadata update <doc_id> --title "New Title"
```

**Expected Result:**
- Metadata operations work
- Updates persist
- Display is clear

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.2: `ragged search`

**Steps:**
```bash
ragged search --filter "format:pdf"
ragged search --filter "date>2024-01-01"
```

**Expected Result:**
- Filters work correctly
- Results match criteria
- Multiple filters combinable

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.3: `ragged history`

**Steps:**
```bash
ragged history list
ragged history replay <query_id>
ragged history search "term"
```

**Expected Result:**
- History tracked
- Replay works identically
- Search functional

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.4: `ragged cache`

**Steps:**
```bash
ragged cache status
ragged cache clear
```

**Expected Result:**
- Cache status shown
- Clear operation works
- Statistics displayed

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.5: `ragged export/import`

**Steps:**
```bash
ragged export backup.zip
ragged clear --no-confirm
ragged import backup.zip
```

**Expected Result:**
- Export creates backup
- Import restores fully
- Data integrity maintained

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 4. Configuration Commands

### Test Case 4.1: `ragged config show`

**Steps:**
```bash
ragged config show
```

**Expected Result:**
- All settings displayed
- Values formatted clearly
- Sensitive data masked/omitted

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 4.2: `ragged config set-model`

**Steps:**
```bash
ragged config set-model --llm llama2
ragged config set-model --embedding all-MiniLM-L6-v2
```

**Expected Result:**
- Model updated
- Changes persist
- Validation occurs

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 4.3: `ragged validate`

**Steps:**
```bash
ragged validate
```

**Expected Result:**
- Configuration validated
- Errors clearly reported
- Suggestions provided

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 5. Diagnostics Commands

### Test Case 5.1: `ragged health`

**Steps:**
```bash
ragged health
```

**Expected Result:**
- Service status shown
- Clear indicators (✓/✗)
- Connection details
- Troubleshooting hints if failed

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 5.2: `ragged env-info`

**Steps:**
```bash
ragged env-info
```

**Expected Result:**
- System information displayed
- Python version, OS, etc.
- Dependency versions
- Useful for debugging

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 6. Shell Completion (v0.2.8+)

### Test Case 6.1: Install Completion (Bash)

**Steps:**
```bash
ragged completion --install bash
source ~/.bashrc
ragged <TAB>
```

**Expected Result:**
- Completion script installed
- Commands auto-complete
- Arguments auto-complete
- File paths complete

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 6.2: Install Completion (Zsh)

**Steps:**
```bash
ragged completion --install zsh
# Restart shell or source config
ragged <TAB>
```

**Expected Result:**
- Works in zsh
- Command completion functional
- Descriptions shown (if supported)

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 7. Help & Documentation

### Test Case 7.1: `ragged --help`

**Steps:**
```bash
ragged --help
```

**Expected Result:**
- All commands listed
- Brief descriptions
- Usage examples
- Version shown

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 7.2: Command-Specific Help

**Steps:**
```bash
ragged add --help
ragged query --help
```

**Expected Result:**
- Detailed command help
- All options explained
- Examples provided
- Clear formatting

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 8. Error Handling

### Test Case 8.1: Invalid Command

**Steps:**
```bash
ragged invalidcommand
```

**Expected Result:**
- Clear error message
- Suggests correct command
- Shows available commands

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 8.2: Missing Arguments

**Steps:**
```bash
ragged add
# (without file argument)
```

**Expected Result:**
- Clear error about missing argument
- Shows usage
- Doesn't crash

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 8.3: Invalid File Path

**Steps:**
```bash
ragged add /nonexistent/file.pdf
```

**Expected Result:**
- File not found error
- Clear message
- Suggests checking path

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 8.4: Service Unavailable

**Steps:**
```bash
# Stop Ollama
ragged query "test"
```

**Expected Result:**
- Service unavailable error
- Explains which service
- Provides troubleshooting

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 9. Verbosity Control

### Test Case 9.1: Quiet Mode

**Steps:**
```bash
ragged add file.pdf --quiet
```

**Expected Result:**
- Minimal output
- Only essential info
- No progress indicators

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 9.2: Verbose Mode

**Steps:**
```bash
ragged add file.pdf --verbose
```

**Expected Result:**
- Detailed output
- Debug information
- Step-by-step progress

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 10. Output Colours

### Test Case 10.1: Colour Support

**Steps:**
1. Run various commands
2. Observe output colours

**Expected Result:**
- Success messages green
- Errors red
- Warnings yellow
- Info blue/cyan
- Readable contrast

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 10.2: No Colour Mode

**Steps:**
```bash
ragged list --no-color
```

**Expected Result:**
- No ANSI colour codes
- Plain text output
- Still readable

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## Summary

**Total Test Cases:** 35
**Passed:** ____
**Failed:** ____
**N/A:** ____

**Pass Rate:** ____%

---

## Issues Found

| Issue # | Command | Description | Severity |
|---------|---------|-------------|----------|
| 1 | | | ☐ Critical ☐ High ☐ Medium ☐ Low |
| 2 | | | ☐ Critical ☐ High ☐ Medium ☐ Low |
| 3 | | | ☐ Critical ☐ High ☐ Medium ☐ Low |

---

## Usability Notes

[Notes on CLI usability, suggestions for improvements]

---

**Tested By:** ____________________
**Date:** ____________________
**Shell/OS:** ____________________
**ragged Version:** ____________________

---

**Maintained By:** ragged development team
