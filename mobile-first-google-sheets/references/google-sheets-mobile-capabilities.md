# Google Sheets Mobile Capability Evidence

Evidence snapshot: 2026-09-27.

## Official Google sources

1. Android freeze/group/hide/merge support:
   https://support.google.com/docs/answer/9060449?co=GENIE.Platform%3DAndroid&hl=en
2. Android conditional formatting and custom-formula support:
   https://support.google.com/docs/answer/78413?co=GENIE.Platform%3DAndroid&hl=en
3. Android checkboxes:
   https://support.google.com/docs/answer/7684717?co=GENIE.Platform%3DAndroid&hl=en
4. Android dropdown/data validation:
   https://support.google.com/docs/answer/186103?co=GENIE.Platform%3DAndroid&hl=en
5. Android sorting/filtering; filter views are desktop-only:
   https://support.google.com/docs/answer/3540681?co=GENIE.Platform%3DAndroid&hl=en
6. Sheets performance guidance; reduce repeated expressions, volatile functions, and unnecessary conditional formatting:
   https://support.google.com/docs/answer/11468464?hl=en-GB
7. Gemini in Sheets can perform formatting, checkbox/dropdown, filter, and freeze actions; native Sheets is preferred for these workflows:
   https://support.google.com/docs/answer/14356410?hl=en

## Skill interpretation

- Android supports freeze, validation/dropdowns, checkboxes, filters, and conditional formatting, but support does not mean every feature should be used.
- Filter views are not an Android-first navigation primitive.
- Native Google Sheets verification remains necessary after XLSX conversion.
- Volatile formulas and conditional formatting should be budgeted because recalculation/format evaluation affects performance.
- Design must remain usable if imported freeze/protection behavior changes during conversion.

## Native conversion integrity notes

These are workflow requirements, not claims that every conversion will fail:
- Verify the spreadsheet timezone after import/conversion; defaults can differ from the intended operating timezone.
- Re-check merged ranges and freeze state after conversion.
- Enumerate conditional-format rules rather than assuming source cleanup carried through.
- Apply/verify protection natively when the operational model depends on protected formulas or backend sheets.
- Re-read affected native state after material writes; request success is not equivalent to behavioral verification.