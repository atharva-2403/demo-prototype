# ClearClaim — Live Judge Demo Checklist

## Setup
- [ ] Run `./run_demo.sh` from the project root.
- [ ] Ensure the script prints the URLs and does not warn about a missing `ANTHROPIC_API_KEY`.
- [ ] Open a browser and navigate to `http://localhost:5173`. You should see the ClearClaim AI File Upload dropzone.

## Scenario 1: Valid 837P Processing
- [ ] Locate the file `clearclaim-backend/tests/sample_files/valid_837p.edi`.
- [ ] Drag and drop this file into the browser.
- [ ] **Expectation**: The file should parse correctly, showing a green "VALID" tag in the Metadata Bar. The Segment Tree should be explorable, and no Error Dashboard should appear.

## Scenario 2: Malformed 837I Processing
- [ ] Refresh the page to clear the current file.
- [ ] Locate the file `clearclaim-backend/tests/sample_files/malformed_837i.edi`.
- [ ] Drag and drop this file into the browser.
- [ ] **Expectation**: The Metadata Bar should show a red "6 ERRORS" tag.
- [ ] Verify the Error Dashboard appears and lists the following 6 errors clearly in plain English:
  - [ ] `INVALID_NPI`: Flagging the `1234567890` value.
  - [ ] `INVALID_DATE_FORMAT`: Flagging the `01152023` value.
  - [ ] `MISSING_BILLING_PROVIDER`: Flagging the missing `NM1` segment in Loop 2010AA.
  - [ ] `INVALID_FACILITY_CODE`: Flagging the `XX` code in `CLM05-1`.
  - [ ] `CLM_AMOUNT_MISMATCH`: Flagging the `400` vs `350.0` sum discrepancy.
  - [ ] `MISSING_ROI_CODE`: Flagging the missing Release of Information Code in `CLM09`.

## Scenario 3: AI Chat Interaction (on Malformed 837I)
- [ ] With the `malformed_837i.edi` file still loaded, navigate to the ClearClaim AI Assistant panel.
- [ ] Type the following questions and hit Send.
  - [ ] **Question 1**: "Why was this claim rejected?"
    - **Expectation**: The AI should synthesize the 6 validation errors into a cohesive summary using the contextual markdown provided, explicitly mentioning the missing provider loop, amount mismatches, etc.
  - [ ] **Question 2**: "What does CLM_AMOUNT_MISMATCH mean and how do I fix it?"
    - **Expectation**: The AI should explain that the sum of the service line values does not equal the total billed amount in the header, and specifically cite the numbers `400` vs `350.0`.
  - [ ] **Question 3**: "Which line number has the invalid NPI?"
    - **Expectation**: The AI should correctly identify line 5 based on the provided context block.

## Scenario 4: Other EDI Formats
- [ ] Refresh the page.
- [ ] Drag and drop `clearclaim-backend/tests/sample_files/sample_835.edi`.
- [ ] **Expectation**: File parses successfully, and a "Remittance Summary (835)" block appears.
- [ ] Refresh the page.
- [ ] Drag and drop `clearclaim-backend/tests/sample_files/sample_834.edi`.
- [ ] **Expectation**: File parses successfully, and an "Enrollment Summary (834)" block appears.

## Scenario 5: Exports and Auto-fixing (Optional)
- [ ] Click the "Export PDF Report" button and verify a visually-formatted PDF drops in the downloads folder.
- [ ] Under the Error Dashboard, locate an error with an "Auto-Fix" button (e.g. `CLM_AMOUNT_MISMATCH`).
- [ ] Click "Auto-Fix".
- [ ] **Expectation**: The UI should momentarily reflect "Fixing...", then refresh the validation state and decrement the error count.

---
**Note:** If the API key is not configured, the AI Chat Panel will gracefully return an "Error communicating with AI" string. All other offline rules logic will still operate.