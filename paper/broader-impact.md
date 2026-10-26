# Broader impact statement

Draft written 2026-10-27, after the analysis. TMLR asks for this section; it is optional.

This study informs how language models are compared and chosen. Its main practical message,
that the choice of model mattered more than the reasoning setting on this task, could be
over-read in two ways. First, it holds for one open-ended design task, six families and one
26-hour window; it is not evidence that reasoning modes are unhelpful in general, and on
some families the reasoning setting changed scores a great deal. Second, the per-family
scores are not a product ranking. They reflect one prompt, app settings that differed
between vendors (including live web search in three apps) and models that the apps can
change without notice. We report them to explain the variance decomposition, not to
recommend a vendor.

Two findings bear on evaluation practice beyond this paper. Relative to the other raters,
each LLM rater scored its own vendor's answers higher than it scored the other families, by
1.11 and 1.50 points of 18, about the size of the average effect of reasoning mode, so a
study that uses a single LLM judge from a vendor it is comparing can mistake
self-preference for an effect. And two of six models named a
different vendor's model when asked to identify themselves, so a model's self-report is not
reliable evidence of which model answered.

Reasoning modes also use more computation per answer: in the first API check of each
family the reasoning setting used between 1,367 and 23,805 reasoning tokens per call, where
the fast setting used 0 to 131 (a second check on Grok 4.7 was inconclusive). Where reasoning does not improve the answer, the extra cost and energy buy little,
which is one more reason to report the mode.

The study set out to collect no personal data: the 60 answers are model outputs to a
fixed prompt about computer hardware. Three of them nonetheless contain the author's own
account name or home city, which one chat app passed to the model (Section 4.6); no data
about anyone else was collected. The human rater is not named, at their request.
