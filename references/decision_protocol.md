# Decision-complete research protocol

Use this protocol before a research, dataset, or topic-discovery run. It is
self-contained; do not require a personal `/exploring-options` installation.

1. Inspect the target repository and existing dossier before asking anything.
2. List every consequential decision, order them by dependency, and tell the
   user how many remain.
3. Ask one decision at a time. Give only viable options, with the meaningful
   advantage and cost of each.
4. Recommend one option using repository evidence and current methodological
   practice. State the tradeoff explicitly.
5. Record the question, options, recommendation, selection, and downstream
   impact in `runs/<run-id>/manifest.json` under `decision_log`.
6. Recalculate later questions when an answer changes their premises.
7. Begin retrieval only when scope, audience, exclusions, source policy,
   currency cutoff, risk tier, review policy, rights policy, consumers, and
   release criteria are decision-complete.

If the user explicitly asks to proceed before every choice is resolved, record
the recommended default for each remaining choice as an assumption. Never hide
an unresolved choice that could materially change evidence selection or output.
