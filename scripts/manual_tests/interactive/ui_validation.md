# Gradio UI Validation Checklist

**Purpose:** Manual validation of the Gradio web interface for ragged.

**Estimated Time:** 30-45 minutes

**Last Updated:** 2025-11-19

---

## Prerequisites

- [ ] Ragged installed and configured
- [ ] Ollama service running (http://localhost:11434)
- [ ] ChromaDB service running (http://localhost:8001)
- [ ] Gradio UI started (`ragged ui` or `scripts/start_ui.sh`)
- [ ] Test documents available for upload

---

## 1. Initial Load & Layout

### Test Case 1.1: UI Loads Successfully

**Steps:**
1. Open browser to http://localhost:7860
2. Wait for page to load completely

**Expected Result:**
- Page loads without errors
- All UI components visible
- No console errors in browser dev tools

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 1.2: Responsive Layout

**Steps:**
1. Resize browser window to different sizes:
   - Desktop (1920x1080)
   - Tablet (768x1024)
   - Mobile (375x667)
2. Check layout at each size

**Expected Result:**
- Layout adjusts appropriately
- No overlapping elements
- All components accessible
- No horizontal scrolling required

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 2. Document Upload Interface

### Test Case 2.1: Single File Upload

**Steps:**
1. Click "Upload Document" button
2. Select a single PDF file (<10MB)
3. Click "Submit"

**Expected Result:**
- File picker opens
- Upload progress indicator appears
- Success message displays after upload
- Document appears in document list
- Upload time is reasonable (<10 seconds for 5MB file)

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 2.2: Multiple File Upload

**Steps:**
1. Click "Upload Document" button
2. Select multiple files (PDF, MD, TXT, HTML)
3. Click "Submit"

**Expected Result:**
- All files upload successfully
- Progress shown for each file
- Summary of uploads displayed
- All documents appear in list

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 2.3: Folder Upload

**Steps:**
1. Click "Upload Folder" button
2. Select a folder with multiple documents
3. Click "Submit"

**Expected Result:**
- Recursive scan message appears
- All files in folder uploaded
- Nested folder files included
- Summary shows total files processed

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 2.4: Unsupported File Type

**Steps:**
1. Try to upload unsupported file (.exe, .zip, etc.)
2. Observe error handling

**Expected Result:**
- Clear error message
- Explains supported formats
- Doesn't crash UI
- Can try again with valid file

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 3. Query Interface

### Test Case 3.1: Simple Query

**Steps:**
1. Type simple query: "What is RAG?"
2. Click "Submit" or press Enter

**Expected Result:**
- Query processing indicator appears
- Response streams in (word by word)
- Response is relevant and coherent
- Sources are displayed below response
- Response time < 5 seconds

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.2: Complex Query

**Steps:**
1. Type complex query with multiple parts
2. Submit query

**Expected Result:**
- Query handled correctly
- Response addresses all parts
- Multiple sources cited
- Response quality is good

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.3: Query with No Results

**Steps:**
1. Query for content not in documents
2. Observe response

**Expected Result:**
- Graceful handling
- Clear message about no relevant documents
- Suggestion to upload relevant documents
- No crash or error

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 3.4: Empty Query

**Steps:**
1. Submit empty query (just whitespace)
2. Observe behaviour

**Expected Result:**
- Validation prevents submission OR
- Clear error message displayed
- UI remains functional

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 4. Source Citations

### Test Case 4.1: Source Display

**Steps:**
1. Submit query
2. Examine sources displayed

**Expected Result:**
- Sources clearly separated from answer
- Each source shows:
  - Document name/title
  - Relevant excerpt
  - Page number (for PDFs)
  - Relevance score (optional)

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 4.2: Source Expandability

**Steps:**
1. Look for expandable source sections
2. Click to expand/collapse

**Expected Result:**
- Sources can be expanded for more context
- Collapse works smoothly
- Content readable when expanded

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 5. Configuration Panel

### Test Case 5.1: Model Selection

**Steps:**
1. Open model selection dropdown
2. Change LLM model
3. Change embedding model

**Expected Result:**
- Available models listed
- Selection persists
- New queries use new model
- Performance impact documented

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 5.2: Chunking Parameters

**Steps:**
1. Adjust chunk size slider
2. Adjust overlap slider
3. Upload new document

**Expected Result:**
- Sliders work smoothly
- Values update visibly
- New documents use new settings
- Reasonable min/max limits

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 6. Document List Management

### Test Case 6.1: View Document List

**Steps:**
1. Click "View Documents" or equivalent
2. Review list

**Expected Result:**
- All uploaded documents shown
- Document metadata visible:
  - Name
  - Upload date
  - Size
  - Format
- Searchable/filterable

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 6.2: Delete Document

**Steps:**
1. Select a document
2. Click "Delete"
3. Confirm deletion

**Expected Result:**
- Confirmation prompt appears
- Document removed from list
- Document no longer queryable
- Success message displayed

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 7. Error Handling

### Test Case 7.1: Service Unavailable

**Steps:**
1. Stop Ollama service
2. Try to submit query
3. Restart Ollama
4. Try again

**Expected Result:**
- Clear error message
- Explains Ollama unavailable
- Provides troubleshooting hints
- Recovers gracefully when service restored

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 7.2: Network Error

**Steps:**
1. Disconnect network
2. Try various operations
3. Reconnect

**Expected Result:**
- Network errors handled gracefully
- Clear error messages
- Retry capability
- Recovery when network restored

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 8. Performance

### Test Case 8.1: Large File Upload

**Steps:**
1. Upload file >50MB
2. Monitor upload

**Expected Result:**
- Progress indicator works
- Upload completes successfully
- Reasonable time (<2 min for 50MB)
- No timeout errors

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 8.2: UI Responsiveness

**Steps:**
1. Perform various operations rapidly
2. Switch between sections quickly

**Expected Result:**
- UI remains responsive
- No lag or freezing
- Transitions smooth
- No memory leaks (check dev tools)

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 9. Accessibility

### Test Case 9.1: Keyboard Navigation

**Steps:**
1. Navigate UI using Tab key only
2. Try to perform all operations

**Expected Result:**
- All interactive elements focusable
- Focus indicators visible
- Logical tab order
- Can submit forms with Enter
- Can use without mouse

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

### Test Case 9.2: Screen Reader Compatibility

**Steps:**
1. Enable screen reader (VoiceOver, NVDA, etc.)
2. Navigate through UI

**Expected Result:**
- Elements properly labelled
- Content announced clearly
- Forms describable
- Navigation logical

**Actual Result:** ____________________

**Status:** ☐ Pass ☐ Fail ☐ N/A

---

## 10. Browser Compatibility

### Test Case 10.1: Chrome

**Status:** ☐ Pass ☐ Fail ☐ N/A
**Notes:** ____________________

---

### Test Case 10.2: Firefox

**Status:** ☐ Pass ☐ Fail ☐ N/A
**Notes:** ____________________

---

### Test Case 10.3: Safari

**Status:** ☐ Pass ☐ Fail ☐ N/A
**Notes:** ____________________

---

### Test Case 10.4: Edge

**Status:** ☐ Pass ☐ Fail ☐ N/A
**Notes:** ____________________

---

## Summary

**Total Test Cases:** 26
**Passed:** ____
**Failed:** ____
**N/A:** ____

**Pass Rate:** ____%

---

## Issues Found

| Issue # | Description | Severity | Status |
|---------|-------------|----------|--------|
| 1 | | ☐ Critical ☐ High ☐ Medium ☐ Low | ☐ Open ☐ Fixed |
| 2 | | ☐ Critical ☐ High ☐ Medium ☐ Low | ☐ Open ☐ Fixed |
| 3 | | ☐ Critical ☐ High ☐ Medium ☐ Low | ☐ Open ☐ Fixed |

---

## Recommendations

[Notes on improvements, enhancements, or areas of concern]

---

**Tested By:** ____________________
**Date:** ____________________
**Browser/OS:** ____________________
**ragged Version:** ____________________

---

**Maintained By:** ragged development team
