# Array of Thoughts Provider Behavioral Comparison

## Test Configuration

**Concept:** `clinical research participant recruitment`

The Array of Thoughts behavioral test was run against three provider/model combinations:

| Provider      | Model                                  |
| ------------- | -------------------------------------- |
| OpenAI        | `gpt-5.6-luna`                         |
| DeepSeek      | `deepseek-v4-flash` (thinking enabled) |
| Google Gemini | `gemini-2.5-flash`                     |

> The DeepSeek result documented below uses `deepseek-v4-flash` with thinking mode explicitly enabled.

## DeepSeek V4 Flash Comparison Procedure

The provider supports explicit DeepSeek V4 Flash thinking-mode selection without changing the provider-neutral request contract. Both comparison runs use the same model identifier:

```text
deepseek-v4-flash
```

The `DEEPSEEK_THINKING` environment variable controls the request:

| Setting    | DeepSeek request payload                          |
| ---------- | ------------------------------------------------- |
| `enabled`  | `extra_body={"thinking": {"type": "enabled"}}`    |
| `disabled` | `extra_body={"thinking": {"type": "disabled"}}`   |
| absent     | No explicit toggle; preserve the provider default |

The behavioral test prints the selected mode so the output can be audited.

### Non-Thinking Run

```bash
DEEPSEEK_THINKING=disabled \
THOUGHT_GRAPH_PROVIDER=deepseek \
DEEPSEEK_MODEL=deepseek-v4-flash \
python examples/behavior_test.py
```

### Thinking Run

```bash
DEEPSEEK_THINKING=enabled \
THOUGHT_GRAPH_PROVIDER=deepseek \
DEEPSEEK_MODEL=deepseek-v4-flash \
python examples/behavior_test.py
```

Expected audit header:

```text
Provider: deepseek
Model: deepseek-v4-flash
Thinking: enabled
```

or:

```text
Provider: deepseek
Model: deepseek-v4-flash
Thinking: disabled
```

DeepSeek's thinking-mode API separates the mode toggle from the model identifier. The comparison should evaluate the parsed final content while retaining reasoning metadata separately.

The behavioral test evaluates two core Array of Thoughts operations:

1. **Horizontal generation** — decomposition of the root concept into peer-level major dimensions.
2. **Vertical direct-child generation** — decomposition of every horizontal thought into more-specific direct children.

The desired structure is:

```text
Root concept
├── Horizontal sibling
│   ├── Direct child
│   ├── Direct child
│   └── Direct child
├── Horizontal sibling
│   └── ...
└── Horizontal sibling
    └── ...
```

---

# 1. OpenAI — GPT-5.6 Luna

**Provider:** OpenAI
**Model:** `gpt-5.6-luna`

## Horizontal Result

### 1. Participant Eligibility and Targeting

Definition and identification of the populations, eligibility profiles, and recruitment segments relevant to a clinical study.

### 2. Recruitment Sources and Access Channels

The external and institutional pathways through which potential participants can be reached and made aware of a study.

### 3. Recruitment Messaging and Communication

The content, framing, clarity, and communication strategy used to inform prospective participants about study participation.

### 4. Ethical and Regulatory Compliance

The ethical principles, informed-consent requirements, privacy protections, and regulatory standards governing recruitment.

### 5. Enrollment Experience and Participant Engagement

The participant-facing experience from initial interest through screening, consent, enrollment, and continued involvement.

### 6. Recruitment Performance and Equity

The measurement of recruitment outcomes, efficiency, representativeness, access, and inclusion across participant populations.

## Vertical Direct-Child Results

### Participant Eligibility and Targeting

1. Inclusion Criteria Definition
2. Exclusion Criteria Definition
3. Target Population Profiling
4. Eligibility Prescreening
5. Eligibility Confirmation
6. Enrollment Feasibility Assessment

### Recruitment Sources and Access Channels

1. Electronic health record and clinical registry outreach
2. Healthcare provider referrals
3. Community-based recruitment
4. Digital and social media recruitment
5. Institutional and research-site recruitment
6. Participant referral and network-based recruitment

### Recruitment Messaging and Communication

1. Audience-specific recruitment messages
2. Plain-language study explanations
3. Recruitment message channels
4. Culturally responsive recruitment communication
5. Recruitment message compliance
6. Recruitment inquiry and follow-up communication

### Ethical and Regulatory Compliance

1. Informed Consent Procedures
2. Institutional Review Board Approval
3. Participant Privacy and Confidentiality
4. Fair and Non-Coercive Recruitment
5. Vulnerable Population Protections
6. Recruitment Recordkeeping and Reporting

### Enrollment Experience and Participant Engagement

1. Participant-Friendly Study Information
2. Informed Consent Experience
3. Enrollment Process Usability
4. Participant Communication Touchpoints
5. Trust and Relationship Building
6. Recruitment Follow-Up and Retention Handoff

### Recruitment Performance and Equity

1. Enrollment Rate
2. Recruitment Source Effectiveness
3. Screening-to-Enrollment Conversion
4. Recruitment Cost Efficiency
5. Representation of Underrepresented Groups
6. Equitable Recruitment Access

---

# 2. DeepSeek — DeepSeek V4 Flash (Thinking)

**Provider:** DeepSeek
**Model:** `deepseek-v4-flash`
**Thinking:** enabled

## Horizontal Result

### 1. Regulatory and Ethical Framework

Covers the laws, guidances, institutional review board oversight, informed consent requirements, privacy protections, and ethical treatment of vulnerable populations that shape recruitment practices.

### 2. Protocol Design and Feasibility

Covers how study objectives, eligibility criteria, trial phases, procedures, visit burden, and target sample size influence the pool of eligible participants and the practicality of recruiting them.

### 3. Recruitment Strategies and Outreach

Covers the methods and channels used to identify, reach, and encourage potential participants to inquire about a study, including community engagement, healthcare referrals, registries, media, and digital campaigns.

### 4. Site Operations and Enrollment Workflow

Covers the clinical site capabilities, staffing, training, screening and enrollment processes, coordination with care teams, and operational capacity needed to convert interest into formal enrollment.

### 5. Participant Engagement and Experience

Covers communication, trust, barriers, incentives, cultural responsiveness, and the interpersonal factors that shape an individual's interest, willingness, and continued cooperation during the recruitment and enrollment process.

### 6. Data, Metrics, and Technology

Covers recruitment intelligence, electronic health record and registry mining, digital platforms, tracking systems, and performance metrics used to plan, monitor, and improve recruitment across studies and sites.

## Vertical Direct-Child Results

### Regulatory and Ethical Framework

1. IRB/Ethics Committee Review of Recruitment Plans
2. Informed Consent in Recruitment
3. Review of Recruitment Advertising and Materials
4. Privacy and Confidentiality Regulations
5. Safeguards for Vulnerable Populations
6. Equitable Participant Selection

### Protocol Design and Feasibility

1. Eligibility Criteria Development
2. Recruitment Feasibility Assessment
3. Participant Burden and Convenience
4. Study Timeline and Enrollment Milestones
5. Site Selection and Feasibility
6. Study Design Complexity

### Recruitment Strategies and Outreach

1. Community-Based Participatory Outreach
2. Digital and Social Media Recruitment
3. Clinical Trial Registries and Database Matching
4. Provider Referral and Health System Outreach
5. Patient Advocacy and Support Group Partnerships
6. Culturally Tailored and Language-Specific Recruitment

### Site Operations and Enrollment Workflow

1. Pre-screening and Eligibility Assessment
2. Informed Consent Facilitation
3. Screening and Baseline Visit Execution
4. Randomization and Treatment Assignment
5. Enrollment Documentation and Source Data
6. Enrollment Pipeline Tracking and Reporting

### Participant Engagement and Experience

1. Onboarding and Orientation
2. Communication and Check-ins
3. Visit Experience and Convenience
4. Support and Resource Navigation
5. Recognition and Reimbursement
6. Feedback and Continuous Improvement

### Data, Metrics, and Technology

1. EHR Data Mining for Eligibility Screening
2. Recruitment Performance Dashboards
3. Predictive Modeling for Enrollment Forecasting
4. Clinical Trial Management Systems (CTMS) Integration
5. Digital Advertising and Social Media Analytics
6. Patient Registry and Real-World Data Connectivity

---

# 3. Google Gemini — Gemini 2.5 Flash

**Provider:** Gemini
**Model:** `gemini-2.5-flash`

## Horizontal Result

### 1. Target Population Definition

Identifying and characterizing the specific group of individuals eligible and desired for the study, including their demographics, health conditions, potential barriers, and motivators.

### 2. Recruitment Strategy & Design

Developing the overarching plan, methods, channels, messaging, and timelines for reaching and attracting potential participants, tailored to the defined target population.

### 3. Outreach & Engagement Mechanisms

The specific approaches and channels used to connect with potential participants, disseminate study information, generate interest, and initiate contact.

### 4. Screening & Enrollment Pathway

The systematic process from initial contact through eligibility assessment, informed consent acquisition, and final study enrollment.

### 5. Ethical & Regulatory Compliance

Adherence to all relevant ethical principles, institutional policies, and legal regulations governing the protection of human subjects in research during the recruitment process.

### 6. Performance Monitoring & Optimization

Tracking key metrics, analyzing recruitment progress, identifying bottlenecks, and implementing iterative adjustments to improve efficiency and effectiveness.

## Vertical Direct-Child Results

### Target Population Definition

1. Inclusion Criteria Specification
2. Exclusion Criteria Specification
3. Demographic Profile Delineation
4. Disease/Condition Phenotyping
5. Prior Treatment History Parameters
6. Geographic and Logistical Accessibility Parameters

### Recruitment Strategy & Design

1. Target Population Profiling
2. Recruitment Channel & Method Selection
3. Recruitment Material Development
4. Community & Stakeholder Engagement Planning
5. Pre-screening & Eligibility Workflow Design
6. Participant Incentive & Reimbursement Design

### Outreach & Engagement Mechanisms

1. Community-based Outreach Programs
2. Digital and Social Media Campaigns
3. Healthcare Provider Referral Networks
4. Patient Registries and Databases
5. Direct-to-Patient Advertising (DTP)
6. Patient Advocacy Group Collaborations

### Screening & Enrollment Pathway

1. Initial Pre-screening & Eligibility Check
2. Informed Consent Process & Acquisition
3. Comprehensive Clinical Eligibility Assessment
4. Baseline Data Collection & Assessments
5. Study Group Allocation (Randomization/Assignment)
6. Formal Study Enrollment & Registration

### Ethical & Regulatory Compliance

1. IRB/EC Review and Approval of Recruitment Plans
2. Ethical Conduct of Informed Consent for Recruitment
3. Safeguarding Vulnerable Populations in Recruitment
4. Compliance with Recruitment Advertising Regulations
5. Avoiding Undue Inducement and Coercion in Recruitment
6. Privacy and Confidentiality of Potential Participant Data

### Performance Monitoring & Optimization

1. Recruitment Key Performance Indicator (KPI) Tracking
2. Recruitment Funnel Conversion Analysis
3. Recruitment Source ROI Evaluation
4. Clinical Site Recruitment Benchmarking
5. Recruitment Intervention Effectiveness Measurement
6. Predictive Enrollment Forecasting

---

# Comparative Analysis

## Evaluation Principle

For Array of Thoughts, it is not enough that every generated thought is merely relevant to the root concept.

A strong horizontal decomposition should identify **fundamental dimensions of the subject at comparable abstraction levels**.

The evaluation therefore considers:

* sibling consistency
* distinctness
* coverage
* concept relevance
* granularity consistency
* **structural fundamentality**

Vertical generation should additionally preserve:

* direct parent-child relationship
* increased specificity
* scope control
* minimal cross-branch leakage

---

## Condensed Thought Structure Comparison

| Model                            | Horizontal Thought                               | Vertical Direct Children                                                                                                                               |
| -------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **GPT-5.6 Luna**                 | Participant Eligibility and Targeting            | Inclusion Criteria; Exclusion Criteria; Target Population Profiling; Eligibility Prescreening; Eligibility Confirmation; Enrollment Feasibility        |
|                                  | Recruitment Sources and Access Channels          | EHR/Clinical Registries; Provider Referrals; Community Recruitment; Digital/Social Media; Research Sites; Participant Referrals                        |
|                                  | Recruitment Messaging and Communication          | Audience-Specific Messaging; Plain-Language Explanations; Message Channels; Culturally Responsive Communication; Message Compliance; Inquiry/Follow-Up |
|                                  | Ethical and Regulatory Compliance                | Informed Consent; IRB Approval; Privacy/Confidentiality; Non-Coercive Recruitment; Vulnerable Population Protections; Recordkeeping/Reporting          |
|                                  | Enrollment Experience and Participant Engagement | Participant-Friendly Information; Consent Experience; Enrollment Usability; Communication Touchpoints; Trust Building; Retention Handoff               |
|                                  | Recruitment Performance and Equity               | Enrollment Rate; Source Effectiveness; Screening-to-Enrollment Conversion; Cost Efficiency; Representation; Equitable Access                           |
| **DeepSeek V4 Flash (thinking)** | Regulatory and Ethical Framework                 | IRB/Ethics Review; Informed Consent; Recruitment Advertising Review; Privacy/Confidentiality; Vulnerable Population Safeguards; Equitable Selection    |
|                                  | Protocol Design and Feasibility                  | Eligibility Criteria; Recruitment Feasibility; Participant Burden; Enrollment Milestones; Site Feasibility; Design Complexity                          |
|                                  | Recruitment Strategies and Outreach              | Community Outreach; Digital/Social Recruitment; Registries/Database Matching; Provider Referrals; Advocacy Partnerships; Tailored Recruitment          |
|                                  | Site Operations and Enrollment Workflow          | Pre-screening; Consent Facilitation; Screening/Baseline Visits; Randomization; Enrollment Documentation; Pipeline Tracking                             |
|                                  | Participant Engagement and Experience            | Onboarding; Communication; Visit Convenience; Support Navigation; Reimbursement; Feedback                                                              |
|                                  | Data, Metrics, and Technology                    | EHR Eligibility Screening; Performance Dashboards; Enrollment Forecasting; CTMS Integration; Digital Analytics; Registry/Real-World Data               |
| **Gemini 2.5 Flash**             | Target Population Definition                     | Inclusion Criteria; Exclusion Criteria; Demographics; Disease Phenotyping; Treatment History; Geographic/Logistical Accessibility                      |
|                                  | Recruitment Strategy & Design                    | Population Profiling; Channel Selection; Recruitment Materials; Stakeholder Engagement; Pre-Screening Workflow; Incentive Design                       |
|                                  | Outreach & Engagement Mechanisms                 | Community Outreach; Digital/Social Campaigns; Provider Referrals; Registries/Databases; Direct-to-Patient Advertising; Advocacy Groups                 |
|                                  | Screening & Enrollment Pathway                   | Pre-Screening; Informed Consent; Clinical Eligibility Assessment; Baseline Assessment; Study Allocation; Formal Enrollment                             |
|                                  | Ethical & Regulatory Compliance                  | IRB/EC Approval; Ethical Consent; Vulnerable Populations; Advertising Compliance; Coercion/Inducement; Privacy                                         |
|                                  | Performance Monitoring & Optimization            | KPI Tracking; Funnel Conversion; Source ROI; Site Benchmarking; Intervention Effectiveness; Enrollment Forecasting                                     |

## Performance Summary

| Criterion                         | GPT-5.6 Luna | DeepSeek V4 Flash (thinking) | Gemini 2.5 Flash |
| --------------------------------- | ------------ | ---------------------------- | ---------------- |
| Horizontal consistency            | Very strong  | Strong                       | Very strong      |
| Structural fundamentality         | Strong       | Strong                       | **Very strong**  |
| Vertical parent-child consistency | Very strong  | **Very strong**              | **Very strong**  |
| Coverage                          | Very strong  | Very strong                  | Very strong      |
| Granularity consistency           | Strong       | Strong                       | **Very strong**  |
| Cross-branch separation           | Strong       | Strong                       | Strong           |
| Process structure                 | Strong       | Strong                       | **Very strong**  |

## Quantitative Benchmark

The current behavioral runs primarily capture qualitative structure. Future controlled runs should record runtime and token usage so structural quality can be evaluated together with cost and latency.

| Model             | Thinking | Latency | Input Tokens | Output Tokens | Estimated Cost | Structural Score |
| ----------------- | -------- | ------: | -----------: | ------------: | -------------: | ---------------: |
| GPT-5.6 Luna      | —        |     TBD |          TBD |           TBD |            TBD |              TBD |
| Gemini 2.5 Flash  | —        |     TBD |          TBD |           TBD |            TBD |              TBD |
| DeepSeek V4 Flash | disabled |     TBD |          TBD |           TBD |            TBD |              TBD |
| DeepSeek V4 Flash | enabled  |     TBD |          TBD |           TBD |            TBD |              TBD |

Useful derived metrics should eventually include:

* output tokens per generated thought
* total tokens per complete horizontal + vertical run
* estimated cost per complete run
* latency per provider call
* total test latency
* structural score per dollar

These measurements would allow the benchmark to distinguish raw model quality from **quality per unit cost**.

---

# OpenAI GPT-5.6 Luna Analysis

GPT-5.6 Luna produces a noticeably cleaner horizontal structure than the earlier GPT-5 mini run.

Its major branches are:

```text
Eligibility
Sources
Messaging
Compliance
Enrollment experience
Performance
```

These correspond reasonably well to major functional dimensions of clinical research participant recruitment.

The strongest branches are:

* `Participant Eligibility and Targeting`
* `Recruitment Sources and Access Channels`
* `Recruitment Messaging and Communication`
* `Ethical and Regulatory Compliance`

Their vertical decompositions are generally coherent and remain tightly scoped to the parent.

There is still some conceptual blending.

`Enrollment Experience and Participant Engagement` combines several stages:

```text
screening
consent
enrollment
continued involvement
```

This moves somewhat beyond recruitment itself toward retention.

Likewise:

```text
Recruitment Performance and Equity
```

combines operational measurement with representativeness/access concerns.

Those concepts are individually relevant, but they are not necessarily one intrinsic dimension.

### Character

**Compact, operational, disciplined, generally hierarchical.**

### Preliminary Assessment

One of the strongest results in this test. Luna appears particularly good at avoiding excessive thematic branching.

---

# DeepSeek V4 Flash Thinking Analysis

DeepSeek V4 Flash in thinking mode produces a substantially process-oriented hierarchy.

Its horizontal structure is:

```text
Regulatory and Ethical Framework
Protocol Design and Feasibility
Recruitment Strategies and Outreach
Site Operations and Enrollment Workflow
Participant Engagement and Experience
Data, Metrics, and Technology
```

These branches cover the major constraints, planning decisions, execution workflow, participant experience, and operational feedback loop involved in clinical research participant recruitment.

The strongest improvement is the explicit separation of:

```text
Protocol Design and Feasibility
Site Operations and Enrollment Workflow
```

This gives the hierarchy a clearer operational backbone. Eligibility criteria, recruitment feasibility, participant burden, screening, consent, enrollment documentation, and pipeline tracking appear as direct children of appropriate parents rather than being scattered across broad themes.

The vertical results are also tightly scoped. For example:

```text
Site Operations and Enrollment Workflow
    → Pre-screening and Eligibility Assessment
    → Informed Consent Facilitation
    → Screening and Baseline Visit Execution
    → Enrollment Documentation and Source Data
```

This is a coherent parent-child progression from site workflow to specific enrollment activities.

The primary structural weakness is:

```text
Data, Metrics, and Technology
```

This branch combines at least two different conceptual dimensions:

```text
Technology / infrastructure
    → EHR data mining
    → CTMS integration
    → registry connectivity

Measurement / analytics
    → dashboards
    → forecasting
    → advertising analytics
```

Both groups are relevant, but combining implementation technology with measurement and analytics makes this horizontal branch less conceptually pure than the strongest branches in the hierarchy.

There are also a few instances of scope leakage. `Randomization and Treatment Assignment`, for example, can reasonably be considered downstream of recruitment and enrollment rather than a recruitment activity itself.

Despite these issues, the overall hierarchy is substantially more structurally grounded than the earlier DeepSeek output.

### Character

**Process-oriented, operationally coherent, with a small amount of cross-cutting aggregation.**

### Preliminary Assessment

DeepSeek V4 Flash thinking mode produces strong horizontal structure, very strong direct-child relationships, and broad coverage.

The result suggests that explicit thinking mode may materially improve structural decomposition. A paired non-thinking run is required before attributing that improvement confidently to thinking mode itself.

---

# Gemini 2.5 Flash Analysis

Gemini produces the cleanest process-oriented decomposition in this experiment.

Its structure is:

```text
Target Population
↓
Recruitment Strategy
↓
Outreach
↓
Screening & Enrollment
↓
Ethical / Regulatory
↓
Performance Monitoring
```

These dimensions are not strictly chronological, but they correspond closely to the functional architecture of participant recruitment.

A major strength is the explicit:

```text
Screening & Enrollment Pathway
```

branch.

This captures a scientifically and operationally important part of clinical recruitment. DeepSeek also isolates this operational structure, although through its separate protocol-feasibility and site-operations branches.

Its `Target Population Definition` branch is particularly strong:

```text
Inclusion Criteria
Exclusion Criteria
Demographic Profile
Disease Phenotype
Prior Treatment History
Geographic / Logistical Accessibility
```

These children are highly consistent in abstraction level and clearly subordinate to the parent.

The principal weakness is overlap between:

```text
Recruitment Strategy & Design
```

and:

```text
Outreach & Engagement Mechanisms
```

For example, recruitment channel selection appears under strategy while actual channel implementations appear under outreach.

This is not necessarily incorrect. It can be interpreted as:

```text
Strategy
    = deciding how recruitment should work

Outreach
    = mechanisms used to execute that strategy
```

The distinction is defensible, although the prompt could potentially sharpen it further.

### Character

**Process-oriented, structurally coherent, and consistently hierarchical.**

### Preliminary Assessment

Gemini produces the strongest overall hierarchy in this particular run.

---

# Preliminary Ordering

Based strictly on these individual behavioral samples, the current qualitative ordering is:

```text
Gemini 2.5 Flash
> DeepSeek V4 Flash (thinking)
> GPT-5.6 Luna
```

This should **not** yet be interpreted as a robust provider or model ranking.

The differences between the three outputs are relatively small, and each configuration is represented by only one behavioral sample. Normal generation variability could change the ordering across repeated runs.

### Gemini 2.5 Flash

The strongest aspect of the Gemini result is its explicit functional structure:

* target population
* recruitment strategy
* outreach
* screening and enrollment
* regulatory compliance
* performance monitoring

It also maintains particularly consistent vertical granularity.

### DeepSeek V4 Flash (Thinking)

DeepSeek's thinking-mode result has a strong operational backbone:

* protocol design and feasibility
* recruitment strategy
* site operations
* participant engagement
* measurement and technology

Its principal weakness is the compound `Data, Metrics, and Technology` branch.

### GPT-5.6 Luna

Luna produces a disciplined and concise hierarchy with strong vertical consistency.

Its primary weaknesses are:

* compound branches such as `Recruitment Performance and Equity`
* some blending of recruitment and retention
* less explicit process staging than Gemini

Its concision may nevertheless become an important advantage once output-token usage and total cost are measured.

---

# Key Finding

All three models successfully understand the basic Array of Thoughts instruction:

```text
horizontal = peer-level decomposition
vertical = more-specific decomposition beneath a selected parent
```

The main difference is **not whether the models can generate relevant thoughts**.

The more discriminating question is:

> **How well does each model identify the fundamental structure of the concept?**

A model can produce six highly relevant topics while still constructing a weak ontology if those topics represent different kinds of things, such as:

```text
process stage
technology
policy objective
measurement framework
ethical constraint
```

at the same horizontal level.

This suggests that **structural fundamentality should be added permanently to the Array of Thoughts behavioral rubric.**

---

# Current Conclusion

This comparison provides encouraging evidence that `bot0-thought-graph` can produce useful provider-independent hierarchical decomposition.

All three tested models generated recognizable horizontal peer structures and generally valid vertical direct-child relationships.

The strongest qualitative result in this single-sample comparison is Gemini 2.5 Flash, followed closely by DeepSeek V4 Flash with thinking enabled and GPT-5.6 Luna.

However, the current evidence is not sufficient to establish a definitive provider ranking.

The next controlled comparison should include:

```text
GPT-5.6 Luna
Gemini 2.5 Flash
DeepSeek V4 Flash (non-thinking)
DeepSeek V4 Flash (thinking)
```

The DeepSeek enabled/disabled pair is particularly valuable because it holds constant:

```text
provider
model
concept
prompt
breadth
generation API
```

while changing only the thinking-mode configuration.

Repeated runs should then collect both structural-quality scores and quantitative measurements:

```text
structural quality
latency
input tokens
output tokens
estimated API cost
quality per dollar
```

That will allow the benchmark to move from a single-sample qualitative comparison toward a repeatable evaluation of **hierarchical quality, efficiency, and provider economics**.
