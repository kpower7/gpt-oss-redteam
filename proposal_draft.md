# GIC Proposal – Procedural Harm Chains – Power, [PI Last Name]

**Project Title:** Procedural Harm Chains: Multi-Turn Agentic Safety Evaluation of Open-Weight Language Models

**Principal Investigator:** [PI Name], [Title], MIT [Department]
**Student Investigator:** Kevin Power, SM Candidate, MIT [Department]
**Funding Tier:** Innovation ($150,000)
**Duration:** 12 months (June 1, 2026 – May 31, 2027)

---

## 1. Introduction and Motivation

Large language models are rapidly transitioning from conversational assistants to autonomous agents that invoke external tools, execute multi-step plans, and interact with live systems. Frameworks such as OpenAI's function-calling API and the Model Context Protocol (MCP) now routinely expose models to structured tool manifests during inference. This architectural shift introduces a fundamentally new attack surface: safety mechanisms trained primarily on plain-text harmful content may fail to generalize to procedurally-framed, tool-centric requests—even when the underlying harm intent is semantically identical.

Prior empirical work has studied adversarial robustness extensively in single-turn text exchanges, but systematic evaluation of safety under tool-augmented, multi-turn contexts remains nascent. Critically, all existing evaluations are single-turn: the model responds once and the response is classified. This abstraction misrepresents real agentic deployments, where models observe tool execution results, integrate feedback into ongoing plans, and make successive decisions across multiple conversation turns. A model that declines a harmful request in isolation may nonetheless escalate toward harm when presented with synthetic evidence that preceding steps succeeded.

We term this phenomenon **procedural harm chains**: sequences of individually ambiguous model actions that collectively constitute harmful behavior only when observed across multiple turns of tool-augmented interaction. The systematic characterization of procedural harm chains is both technically novel and urgently practical—enterprise agentic deployments across HR automation, financial advising, customer service, and code execution are scaling rapidly while safety frameworks remain anchored to single-turn paradigms.

**Empirical Foundation.** This proposal builds directly on a validated empirical baseline. The *gpt-oss-redteam* pipeline (Power, 2025) conducted 15,600 adversarial generations across 52 prompts spanning 13 harm categories—fraud, discrimination, harassment, self-harm, hate speech, data exfiltration, system sabotage, and six others—comparing plain-text and tool-primed variants under three system configurations. Key findings establish the severity of the problem:

- **Aggregate refusal delta: −33.7 percentage points** when tools are present vs. absent (McNemar's test p < 0.001, Cohen's h = 0.818—a large effect)
- **Category-specific vulnerabilities**: Fraud & Unauthorized Access (Δ = −88.0pp, h = 2.24), Harassment & Abuse (Δ = −71.5pp), Discrimination & Bias (Δ = −65.5pp), Security & Sabotage (Δ = −53.5pp)
- **Cross-model generalization**: GPT-OSS 20B (Δ = −40.2pp), DeepSeek (Δ = −30.6pp), and Claude (Δ = −11.1pp) all show highly significant tool-priming effects (all p < 0.001 with FDR correction), implicating a systematic limitation in current safety training across architectures
- **Category-specific resistance**: Self-harm and hate speech maintain >97% refusal rates even when tool-primed, suggesting harm-type-specific safety mechanisms that do not uniformly generalize

These results establish that tool framing is a systematic, cross-model vulnerability in static single-turn settings. They do not—and cannot—address what happens when tools are simulated to execute, when manifests evolve mid-conversation, or when a model observes incremental success across turns. The proposed research directly closes this gap.

---

## 2. Research Questions

This proposal addresses three primary research questions, each designed to produce both empirical benchmarks and mechanistic insights:

**RQ1 — Escalation:** Do open-weight LLMs escalate harmful behavior across conversation turns when presented with simulated evidence of successful intermediate tool executions? Does the rate of escalation vary by harm category and model family?

**RQ2 — Manifest Dynamics:** How does the introduction, removal, or renaming of tools mid-conversation affect refusal stability? Do models exhibit predictable tool-acquisition strategies—actively seeking newly available capabilities—when pursuing harmful ends?

**RQ3 — Architecture Generalization:** How do procedural harm chain vulnerabilities vary across model families (Llama, Mistral, Qwen, Phi) and parameter scales (7B–70B), and do architectural or training-corpus factors predict robustness?

Together, these questions produce the first open, reproducible benchmark for multi-turn agentic safety evaluation, enabling direct comparison across current and future open-weight models.

---

## 3. Methodology

### 3.1 Multi-Turn Simulation Engine

We extend the existing gpt-oss-redteam pipeline with a **multi-turn simulation engine** that interleaves model responses with configurable synthetic tool execution results. No tools are executed against real systems; synthetic feedback shapes model reasoning without producing real-world consequences. Each conversation proceeds as follows:

1. **Turn 0 (Initiation):** Model receives an adversarial prompt plus a tool manifest under one of three system conditions (null, tool-primed, adversarially-warned)
2. **Turn k (Tool Call):** If the model proposes a tool call, the simulator returns a pre-designed synthetic result from one of three feedback conditions
3. **Turn k+1 (Continuation):** Model observes the synthetic result and generates a subsequent response
4. **Termination:** Conversation ends at a fixed turn limit (3 or 5 turns) or when no further tool calls are proposed

**Synthetic feedback conditions** are designed to span the plausibility space:
- **Success:** Realistic synthetic output confirming execution (e.g., `{"status": "ok", "records_modified": 1247, "timestamp": "..."}`)
- **Failure:** Permission or infrastructure error (e.g., `{"error": "permission_denied", "code": 403}`)
- **Partial:** Ambiguous outcome inviting follow-up (e.g., `{"status": "partial", "completed": 3, "pending": 9}`)

This three-way design tests whether models treat success as license to escalate, treat failure as a natural stopping point, and whether partial results induce novel problem-solving strategies toward harm.

### 3.2 Harm Trajectory Classification

Binary refusal detection is replaced by a **harm trajectory classifier** operating over the full conversation:

- **Turn-level harm score:** Semantic harm rating per model turn using a prompted judge model (GPT-4o as oracle; validated against manual annotations on a 500-conversation sample)
- **Trajectory label:** One of {*Declined*, *Stable*, *Escalating*, *Completed*} based on turn-level score progression
- **Procedural Harm Completeness (PHC):** Binary indicator—did the model reach actionable harm completion across the conversation?
- **Escalation index:** Normalized slope of harm scores across turns (positive = escalating, negative = de-escalating)

Inter-rater reliability between automated classification and human annotation will be reported (target κ > 0.75). This framework provides richer measurement while remaining computationally tractable at scale.

### 3.3 Dynamic Manifest Protocol

To address RQ2, we introduce **manifest evolution events** injected at defined turn boundaries:

- **Expansion:** High-capability tools added mid-conversation (e.g., adding `finance.transfer_funds` or `hr.terminate_employee` after initial exchange)
- **Restriction:** High-risk tools removed to measure whether models attempt to route around the removal
- **Substitution:** Functionally equivalent tool renamed with an innocuous identifier (e.g., `data.archive_record` replacing `db.delete`)

We measure manifest-awareness (whether models redirect toward newly available capabilities) and substitution blindness (whether innocuous naming reduces tool selection rates for harmful ends), directly addressing whether models reason about tool semantics or rely purely on name pattern matching.

### 3.4 Cross-Architecture Benchmarking

We evaluate **16 model configurations** spanning four families and up to four parameter scales:

| Family | 7B | 13B | 34B | 70B |
|--------|-----|------|------|------|
| Llama 3.x | ✓ | ✓ | ✓ | ✓ |
| Mistral/Mixtral | ✓ | ✓ | — | ✓ |
| Qwen 2.5 | ✓ | ✓ | ✓ | ✓ |
| Phi-3/4 | ✓ | ✓ | — | — |

7B–34B models run locally via Ollama; 70B models run on AWS Trainium instances via an existing $44,500 ML Research Award, eliminating the need for cloud budget from this grant.

### 3.5 Experimental Scale

| Dimension | Values | Count |
|-----------|--------|-------|
| Adversarial prompts | 52 existing + 20 new multi-turn-optimized | 72 |
| System conditions | Null, tool-primed, adversarially-warned | 3 |
| Feedback conditions | Success, failure, partial | 3 |
| Turn depths | 3-turn, 5-turn | 2 |
| Tool manifest conditions | Static, dynamic (expansion/restriction/substitution) | 4 |
| Model configurations | 16 | 16 |
| Runs per cell | 20 | — |
| **Estimated conversation turns** | | **~250,000** |

All conversations logged to JSONL with full response objects, tool calls, synthetic feedback, and trajectory labels—preserving complete reproducibility.

---

## 4. Timeline and Milestones

**Months 1–3: Infrastructure and Validation**
- Extend gpt-oss-redteam with multi-turn simulation engine and synthetic feedback system
- Implement and validate harm trajectory classifier (κ > 0.75 target vs. human annotation)
- Design and pilot-test manifest evolution protocol
- *Deliverable:* Open-source multi-turn evaluation framework (v2.0) released on GitHub under CC0

**Months 4–6: Core Data Collection**
- Full experimental run across all 16 models and all conditions
- Interim analysis: escalation rates by model family and harm category; comparison to single-turn baseline
- *Deliverable:* Preprint on multi-turn vs. single-turn refusal comparison; full dataset release

**Months 7–9: Dynamic Manifests and Cross-Architecture Analysis**
- Manifest evolution experiments; manifest-awareness and substitution-blindness analysis
- Cross-architecture statistical analysis (mixed ANOVA: family × scale × harm category)
- Presentation at MIT GenAI Consortium annual symposium
- *Deliverable:* Dataset and analysis scripts released; conference submission (IEEE S&P or CCS)

**Months 10–12: Synthesis and Dissemination**
- Full manuscript finalization and submission
- Policy brief for consortium member companies on agentic deployment risk
- Practitioner-facing evaluation suite documentation
- *Deliverable:* Published or accepted paper; documented, reproducible evaluation suite; policy brief

---

## 5. Broader Impact and Open Science

**Societal Relevance.** The deployment of LLM agents for consequential tasks is accelerating: enterprise automation systems now manage HR workflows, execute financial transactions, and operate customer-facing services. The safety frameworks governing these deployments remain anchored to static, single-turn evaluations that cannot detect the incremental, procedurally-framed harm behaviors this research characterizes. By producing the first open benchmark for multi-turn agentic safety, this project directly equips practitioners and policymakers with evidence for deployment decisions and informs regulatory frameworks for agentic AI systems.

**Open Science Commitment.** All experimental code, datasets, model prompts, synthetic feedback templates, trajectory annotations, and analysis scripts will be released under CC0 license via the existing open-source repository. This satisfies the consortium's Open Source Initiative requirement and ensures that safety researchers globally—including those without access to proprietary evaluation infrastructure—can replicate, extend, and build on this work.

**Relevance to OpenAI.** The GPT-OSS 20B model is a primary subject of this research, and the principal student investigator is the winner of the GPT-OSS 20B challenge, establishing direct domain expertise and connection to OpenAI's open-source initiative. As OpenAI expands tool-augmented and agentic product offerings, cross-architecture benchmarks grounded in reproducible local evaluation provide a complementary, independently-produced safety signal to internal red-teaming. Results will be made available to OpenAI as a consortium member for integration into model development and safety evaluation workflows.

**Investigator Qualifications.** Kevin Power (SM candidate, MIT) designed and implemented the gpt-oss-redteam evaluation pipeline, conducted the 15,600-generation empirical study, and authored the associated IEEE-format research paper and thesis proposal. His win of the GPT-OSS 20B challenge demonstrates recognized expertise directly at the intersection of open-weight model evaluation and safety. The work is supported by [PI Name], [title], whose research group focuses on [PI research area].

**Computing Infrastructure.** The project leverages an existing AWS ML Research Award ($44,500 in Trainium credits) for 70B-scale inference, ensuring the $150,000 budget is focused on personnel, research time, and dissemination rather than cloud compute.

---

*Contact: [PI email] | [Kevin's MIT email]*
*Submission via InfoReady portal | PDF formatted per GIC guidelines*
