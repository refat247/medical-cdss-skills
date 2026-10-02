# v1.0.0 Gap Analysis Against the Actual MI Workflow

**Proven predecessor:** `evidence-locked-clinical-pptx-builder v1.0.0`.

| Required from actual MI workflow | Present in v1.0.0 | Missing / partial | Rebuild decision |
|---|---|---|---|
| Hard source lock / no invention | Yes | Context/visual classes not sufficiently typed | Retain core; expand contract |
| Exhaustive decision-node extraction | Partial | No explicit tables/figures/algorithm/exceptions/special-population completeness contract | Rebuild extraction gate |
| Recommendation-table completeness | Partial | Not a first-class auditable requirement | Add explicit table-row accounting |
| Extraction audit -> repair -> re-audit -> freeze | Partial | Arithmetic reconciliation/section coverage not fully specified | Expand and freeze with hashes |
| Large case libraries | Conceptually yes | Schemas/tooling light for hundreds of cases | Add scalable schemas/validators |
| Case deduplication | Partial | No KEEP/MERGE/SPLIT/DROP/CLARIFY engine/tool | Add adjudication contract + duplicate detector |
| Coverage matrix | Partial | Simple node coverage only; no reconciliation/conflict/explanatory-only accounting | Expand coverage model |
| Cross-source reconciliation | Conceptually yes | No deterministic relationship validator | Add validator + explicit source-language preservation |
| Conflict/terminology register | Yes conceptually | Limited enforcement | Make required artifact in multi-source case mode |
| Corrections / errata | No | No correction register/supersession scope | Add correction pipeline and validator |
| Audience prioritization | Partial | No dedicated schema/validation | Add artifact/schema |
| Teaching architecture | Partial | No explicit anchor/extended/advanced/reference contract | Expand architecture layer |
| Storyboard construction | Partial | No dedicated schema or validator | Add storyboard and case-to-slide mapping artifacts |
| Case-first pedagogy | Yes | Needed stronger definition beyond adding vignettes | Expand supported case patterns |
| Standard non-case build | No explicit mode | Full pipeline could be overused | Add `BUILD_STANDARD` |
| Inspect/patch | No explicit modes | Read-only vs bounded-edit scope not formalized | Add `INSPECT` / `PATCH` |
| Corpus build | No explicit mode | Case corpus not independently routable | Add `CORPUS_BUILD` |
| Derivative deck engine | Partial | No clinical fingerprint/mutation guard; local-resource focus not explicit | Add derivative integrity and context typing |
| Case occurrence maps | Yes, basic | v1 parser assumes MI-style IDs | Generalize configurable ID regex |
| Source locking | Yes | Operational/local constraints and visual assets could drift into evidence | Add typed context/source classes |
| Source figures / external visuals | Partial | Permission/copyright and evidence role not fully modelled | Add visual asset register |
| Speaker notes | Presence + contract | XML presence could be mistaken for semantic fidelity | Separate presence audit from evidence/provenance audit |
| Automated PPTX preflight | Weak | Primarily bounds/global font; weak overlap/image/title/placeholder coverage | Replace with richer preflight |
| Overflow/text fit | Weak | No reliable certification | Add heuristic warnings + mandatory render review |
| Projector visibility | Partial | No enforceable full visual ledger | Add projector/UI contract + 100% ledger |
| 100% slide rendering | Stated | No deterministic render coverage gate | Add `render_qa_gate.py` |
| 100% individual visual inspection | Not enforceable | Contact sheet could be over-trusted | Add per-slide ledger; contact sheet non-certifying |
| Independent visual QA | No | Missing second-runtime handoff and adjudication flow | Add formal preferred gate/template |
| RENDER-UNCERTIFIED status | No | Could falsely imply PASS when renderer/font fidelity absent | Add hard release status |
| Repair -> rerender -> re-audit | Present conceptually | No ledger/gate enforcing final full rerender | Strengthen final release sequence |
| Clinical/provenance lint | Partial | Local-context/evidence separation not deterministic | Add clinical lint/source whitelist checks |
| Derivative canonical integrity | Partial | No stable clinical fingerprint comparison | Add fingerprint validator |
| Final canonical promotion | Yes | Did not require explicit visual-certification evidence/independent status | Strengthen promotion record |
| Modular Slide Bank | Yes conceptually | Parser/product metadata limited | Retain and generalize |
| Closure/hashes | Yes | Good component | Retain and test |
| Failure/adversarial audit | Partial | Not a formal release artifact | Add independent adversarial audit + repair + re-audit |
| Handoff/resume | Yes | Mode and lifecycle state could blur | Separate mode from pipeline state |
| Example configurations | No (MI closed-state only) | Four requested example classes absent | Add five required examples |
| Regression fixtures | No | No representative clipped/tiny/context/correction/mutation fixtures | Add synthetic failure corpus |
| Version/provenance | Yes | Major new semantics require migration plan | Preserve lineage; bump to v2.1.0 |

## Conclusion

v1.0.0 had the correct high-level direction and several useful deterministic utilities, but it did not fully encode or enforce the workflow that the MI project actually required. The correct action is a **major rebuild to v2.1.0**, retaining good components where appropriate rather than discarding them.
