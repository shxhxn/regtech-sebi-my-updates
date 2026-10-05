# SEBI-REGTECH LinkedIn post

Upload `SEBI-REGTECH-LinkedIn-Carousel.pdf` as a **document post** for the swipe experience. Use the document title **SEBI-REGTECH: A walkthrough of the compliance dashboard**. Paste `caption.txt` into the post. Replace the plain-text name Zayed Jawaid with a LinkedIn @mention selected from the mention picker. Use [Zayed Jawaid's profile](https://www.linkedin.com/in/zayed-jawaid-250985379/) to confirm the correct person.

The caption includes the [project repository](https://github.com/shxhxn/regtech-sebi-my-updates).

The `images` folder contains the numbered slides if you prefer a photo post. Upload them in numerical order. The PDF is the recommended format for this particular walkthrough, because it preserves the page order and portrait layout. The local `screenshots` folder preserves real captures from the running app and is excluded from Git along with temporary build files and the duplicate ZIP archive.

## Exact slide order and website evidence

| Slide | Heading | Actual website image | Point the reader should understand |
| --- | --- | --- | --- |
| 1 | SEBI circulars become clear compliance tasks | Overview header and KPI strip, with a close view of priority obligations | The prototype helps Investment Adviser compliance teams review and track extracted obligations. |
| 2 | Each obligation has an action and evidence | All Obligations search for “annual audit”, with one record expanded | A team can find a task, see expected evidence and inspect its source. |
| 3 | Source checks make review visible | Trust & Verification match counts and a matched source excerpt | The saved demo has 277 grounded quotations, 14 partial matches and 8 review flags. |
| 4 | Duties organised by when they recur | What's Due with Recurring selected and the monthly complaint disclosure expanded | Recurrence and trigger categories help organise work. Exact dates require additional handling. |
| 5 | A register for tracking progress | My Register's firm selector and an expanded obligation's saved status | A team can change and save review status. Demo completion percentages are user-entered. |
| 6 | Circular changes shown before and after | What Changed's expanded PAN obligation, focused on before/after source text | Related obligations can be compared across versions for human review. |
| 7 | New circulars enter the update workflow | Overview's Automation panel and recorded pipeline status | The monitor and local processing pipeline connect source discovery to refreshed outputs. |
| 8 | Structured rules for downstream systems | Pipeline Operations' sample rule | The output contains trigger, action, evidence and breach-review fields. |
| 9 | Pipeline history with integrity checks | Trust & Audit's hash-chain entries | The verifier detects modifications that break the retained hash chain. |

## Presentation decisions

- One feature and one reader benefit per slide.
- Actual browser screenshots, with focus crops. No generated website interfaces, decorative illustrations or fabricated results.
- Large headings, a restrained navy/blue palette and portrait pages. Dense screenshot text is supporting evidence; the large slide text explains the feature without requiring the reader to decode the interface.
- Name the intended user early: Investment Adviser compliance teams. Avoid claiming the full workflow supports every regulated firm.
- Credit Zayed and mention the hackathon once in the caption. The competition outcome does not need to be part of a product walkthrough. Do not claim selection, prizes, SEBI approval or endorsement.
- Keep the caption detailed and the slides concise. Use the five hashtags at the end of the caption. Tag Zayed through his actual LinkedIn profile. Do not tag unrelated accounts simply to seek reach.

## What the project analysis established

The README describes the original 2024/2025 demo. The current saved output is a later Investment Adviser dataset from the February 2026 master circular. It contains 299 obligations, with 291 in the grounded or partial bands and 8 flagged. `291 / 299 = 97.3%` is a quotation-match measure. It is not a measured legal interpretation accuracy score, extraction recall, or proof that all obligations were captured.

The saved change report compares the 269-obligation archived 2025 extraction with the 299-obligation 2026 extraction. It reports 101 added, 138 modified, 71 removed and 60 reworded entries. The interface still hard-codes the years 2024 and 2025. The carousel focuses on the actual before/after record and avoids repeating those obsolete labels or presenting detected changes as confirmed legal changes.

The Overview ingestion card selects the last downloaded circular, which is a Stock Broker download, beside metrics from the Investment Adviser dataset. The carousel's Overview crops exclude that misleading combination. No application source or saved compliance data was changed to produce the slides.

“Gaps” come from missing extracted evidence descriptions and absent deadline fields on triggered records. They are not an audit of a firm's uploaded documents. My Register currently changes statuses; it does not provide an evidence-upload or owner-assignment workflow. Rule objects are generated for downstream use; this is not automatic real-world enforcement. The monitor reads SEBI listings, and the full processing path is wired for Investment Advisers. Stock Broker processing in that automatic path is download-only. The audit verifier checks retained hashes; the project does not establish independently anchored or immutable storage.

## Research and engagement

I reviewed public product posts rather than treating generic carousel advice as proof of performance:

1. [Linear: Product Intelligence launch](https://www.linkedin.com/posts/linearapp_introducing-product-intelligence-ai-assisted-activity-7361778355756486658-_3e0). Names concrete jobs the feature handles and identifies its preview status. Adaptation here: explain the actual user task on each slide and state prototype scope.
2. [Linear: UI redesign](https://www.linkedin.com/posts/linearapp_we-redefined-the-foundational-layers-of-linear-activity-7179202393891311617-SNdO). Presents the application and offers implementation context. Adaptation here: show actual screens and place technical detail after the product explanation.
3. [Wecan: Compliance Copilot demo](https://www.linkedin.com/posts/wecangroup_ai-is-starting-to-significantly-simplify-activity-7441717881471533056-_fAB). Walks through concrete compliance workflows using a product demonstration. Adaptation here: arrange the carousel as a workflow a compliance team can follow.

These public pages did not provide reliable comparable impression and reaction data. They cannot establish what caused higher likes or predict 100 likes for this account. Their presentation patterns informed the design; they are not evidence of an engagement formula.

[LinkedIn's document upload guidance](https://www.linkedin.com/help/linkedin/answer/a519831) supports PDF uploads, recommends PDF for quality, and explains adding a document title and post description. It currently lists a 100 MB / 300-page limit, well above this carousel.

For this post, my editorial recommendation is to lead with the firm's problem, show working screens, credit the collaborator and ask one question that invites relevant feedback. Publish when you can respond to comments, answer specific questions with product evidence, and invite Zayed to add his own account of the collaboration if he wants to. There is no supported basis here for a guaranteed posting time, mandatory first-comment link trick or fixed reaction count.

If you want to assess performance afterwards, compare impressions, reactions, comments and profile visits with your prior project post at the same elapsed time. Raw likes alone cannot explain whether the presentation or the size of the reached audience changed.
