# Array of Thoughts Provider Behavioral Comparison

## Test Configuration

**Concept:** `clinical research participant recruitment`

The original Array of Thoughts behavioral test was run against three provider/model combinations:

| Provider      | Model              |
| ------------- | ------------------ |
| OpenAI        | `gpt-5.6-luna`     |
| DeepSeek      | `deepseek-chat`    |
| Google Gemini | `gemini-2.5-flash` |

> Note: the recorded DeepSeek result below uses the legacy `deepseek-chat` identifier. It is retained as historical evidence; it is not a V4 Flash thinking-mode result.

## DeepSeek V4 Flash comparison procedure

The provider now supports explicit DeepSeek V4 Flash thinking-mode selection without changing the provider-neutral request contract. Both runs use the same model identifier:

```text
deepseek-v4-flash
```

The `DEEPSEEK_THINKING` environment variable controls the request:

| Setting | DeepSeek request payload |
| ------- | ------------------------ |
| `enabled` | `extra_body={"thinking": {"type": "enabled"}}` |
| `disabled` | `extra_body={"thinking": {"type": "disabled"}}` |
| absent | No explicit toggle; preserve the provider default |

The behavioral test prints the selected mode so the output can be audited. The two controlled comparison runs are:

```bash
DEEPSEEK_THINKING=disabled \
THOUGHT_GRAPH_PROVIDER=deepseek \
DEEPSEEK_MODEL=deepseek-v4-flash \
python examples/behavior_test.py
```

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
Thinking: disabled
```

DeepSeek documents `thinking.type` as the mode toggle and returns thinking output separately as `reasoning_content`; the comparison should evaluate the parsed final content and retain reasoning metadata separately. See the [DeepSeek thinking-mode documentation](https://api-docs.deepseek.com/guides/thinking_mode).

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

# 2. DeepSeek — DeepSeek Chat

**Provider:** DeepSeek
**Model:** `deepseek-chat`

## Horizontal Result

### 1. Regulatory and Ethical Frameworks

Covers the laws, guidelines, and ethical principles governing recruitment, including informed consent, institutional review boards, data protection, and vulnerable population protections.

### 2. Recruitment Strategies and Outreach

Encompasses methods and channels to identify and engage potential participants, such as community outreach, digital marketing, clinical trial registries, and partnerships with patient advocacy groups.

### 3. Patient Engagement and Retention

Focuses on building trust, communicating study details, addressing patient concerns, and maintaining motivation and adherence throughout the trial to reduce dropout rates.

### 4. Diversity, Equity, and Inclusion in Recruitment

Addresses the systematic inclusion of underrepresented populations, cultural competence, and strategies to overcome barriers related to race, ethnicity, gender, age, and socio-economic status.

### 5. Data and Technology for Recruitment

Involves the use of electronic health records, predictive analytics, artificial intelligence, and digital platforms to identify eligible participants, streamline screening, and optimize recruitment efficiency.

### 6. Metrics, Monitoring, and Quality Management

Covers the measurement of recruitment performance, benchmarking, tracking key performance indicators, and ensuring quality and compliance throughout the recruitment process.

## Vertical Direct-Child Results

### Regulatory and Ethical Frameworks

1. Institutional Review Board (IRB) Approval
2. Informed Consent Process
3. Vulnerable Population Protections
4. HIPAA and Data Privacy Compliance
5. Equitable Participant Selection
6. Advertising and Recruitment Material Standards

### Recruitment Strategies and Outreach

1. Digital and social media advertising
2. Community-based partnerships and engagement
3. Provider and clinician referrals
4. Patient registries and database mining
5. Direct mail and phone outreach
6. In-person and event-based recruitment

### Patient Engagement and Retention

1. Tailored communication channels
2. Incentive and compensation structures
3. Patient feedback and satisfaction loops
4. Peer support and community building
5. Flexible visit scheduling and remote options
6. Health literacy and educational materials

### Diversity, Equity, and Inclusion in Recruitment

1. Culturally tailored outreach messaging
2. Community-based participatory recruitment strategies
3. Reducing implicit bias in eligibility criteria
4. Addressing socioeconomic barriers to participation
5. Inclusive digital recruitment practices
6. Measurement and accountability for diversity goals

### Data and Technology for Recruitment

1. Electronic Health Record (EHR) Screening Algorithms
2. Patient Recruitment Registries and Matching Platforms
3. Social Media and Digital Advertising Analytics
4. Mobile Health (mHealth) and Wearable Device Data
5. Predictive Modeling and Machine Learning for Participant Risk
6. Decentralized Trial Technology and Remote Consent Tools

### Metrics, Monitoring, and Quality Management

1. Recruitment funnel metrics
2. Real-time monitoring dashboards
3. Site performance benchmarking
4. Protocol feasibility and target feasibility reviews
5. Quality assurance audits for recruitment processes
6. Corrective and preventive actions (CAPA) for recruitment issues

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

## Summary Comparison


### Condensed Thought Structure Comparison

| Model                | Horizontal Thought                               | Vertical Direct Children                                                                                                                                   |
| -------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **GPT-5.6 Luna**     | Participant Eligibility and Targeting            | Inclusion Criteria; Exclusion Criteria; Target Population Profiling; Eligibility Prescreening; Eligibility Confirmation; Enrollment Feasibility            |
|                      | Recruitment Sources and Access Channels          | EHR/Clinical Registries; Provider Referrals; Community Recruitment; Digital/Social Media; Research Sites; Participant Referrals                            |
|                      | Recruitment Messaging and Communication          | Audience-Specific Messaging; Plain-Language Explanations; Message Channels; Culturally Responsive Communication; Message Compliance; Inquiry/Follow-Up     |
|                      | Ethical and Regulatory Compliance                | Informed Consent; IRB Approval; Privacy/Confidentiality; Non-Coercive Recruitment; Vulnerable Population Protections; Recordkeeping/Reporting              |
|                      | Enrollment Experience and Participant Engagement | Participant-Friendly Information; Consent Experience; Enrollment Usability; Communication Touchpoints; Trust Building; Retention Handoff                   |
|                      | Recruitment Performance and Equity               | Enrollment Rate; Source Effectiveness; Screening-to-Enrollment Conversion; Cost Efficiency; Representation; Equitable Access                               |
| **DeepSeek Chat**    | Regulatory and Ethical Frameworks                | IRB Approval; Informed Consent; Vulnerable Population Protections; HIPAA/Data Privacy; Equitable Selection; Advertising Standards                          |
|                      | Recruitment Strategies and Outreach              | Digital/Social Advertising; Community Partnerships; Clinician Referrals; Registries/Databases; Mail/Phone; Events                                          |
|                      | Patient Engagement and Retention                 | Communication Channels; Incentives; Feedback; Peer Support; Flexible Scheduling; Health Literacy                                                           |
|                      | Diversity, Equity, and Inclusion                 | Culturally Tailored Messaging; Community-Based Recruitment; Eligibility Bias; Socioeconomic Barriers; Inclusive Digital Recruitment; Diversity Measurement |
|                      | Data and Technology                              | EHR Screening; Matching Platforms; Digital Analytics; mHealth/Wearables; Predictive Modeling; Decentralized Trial Technology                               |
|                      | Metrics, Monitoring, and Quality                 | Funnel Metrics; Dashboards; Site Benchmarking; Feasibility Reviews; QA Audits; CAPA                                                                        |
| **Gemini 2.5 Flash** | Target Population Definition                     | Inclusion Criteria; Exclusion Criteria; Demographics; Disease Phenotyping; Treatment History; Geographic/Logistical Accessibility                          |
|                      | Recruitment Strategy & Design                    | Population Profiling; Channel Selection; Recruitment Materials; Stakeholder Engagement; Pre-Screening Workflow; Incentive Design                           |
|                      | Outreach & Engagement Mechanisms                 | Community Outreach; Digital/Social Campaigns; Provider Referrals; Registries/Databases; Direct-to-Patient Advertising; Advocacy Groups                     |
|                      | Screening & Enrollment Pathway                   | Pre-Screening; Informed Consent; Clinical Eligibility Assessment; Baseline Assessment; Study Allocation; Formal Enrollment                                 |
|                      | Ethical & Regulatory Compliance                  | IRB/EC Approval; Ethical Consent; Vulnerable Populations; Advertising Compliance; Coercion/Inducement; Privacy                                             |
|                      | Performance Monitoring & Optimization            | KPI Tracking; Funnel Conversion; Source ROI; Site Benchmarking; Intervention Effectiveness; Enrollment Forecasting                                         |


### Performance Summary
| Criterion                         | GPT-5.6 Luna | DeepSeek Chat | Gemini 2.5 Flash |
| --------------------------------- | ------------ | ------------- | ---------------- |
| Horizontal consistency            | Very strong  | Moderate      | Very strong      |
| Structural fundamentality         | Strong       | Moderate      | **Very strong**  |
| Vertical parent-child consistency | Very strong  | Strong        | **Very strong**  |
| Coverage                          | Very strong  | Strong        | Very strong      |
| Granularity consistency           | Strong       | Moderate      | **Very strong**  |
| Cross-branch separation           | Strong       | Moderate      | Strong           |
| Process structure                 | Strong       | Moderate      | **Very strong**  |

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

### Preliminary assessment

One of the strongest results in this test. Luna appears particularly good at avoiding excessive thematic branching.

---

# DeepSeek Analysis

DeepSeek generates individually relevant topics, but its horizontal ontology is less structurally fundamental.

The largest issue is the elevation of:

```text
Diversity, Equity, and Inclusion in Recruitment
```

and:

```text
Data and Technology for Recruitment
```

to top-level sibling status.

Both are relevant to recruitment, but they behave more like **cross-cutting concerns, methods, or implementation characteristics** than fundamental components of the recruitment process.

For example, technology can appear throughout:

```text
Eligibility
    → EHR screening

Outreach
    → digital advertising

Screening
    → matching platforms

Enrollment
    → remote consent

Monitoring
    → analytics
```

Similarly, representativeness and access can appear across targeting, outreach, ethics, operational accessibility, and performance measurement.

Promoting these concerns to the same level as recruitment strategy or regulatory requirements therefore weakens the ontology.

Another weakness is the absence of explicit first-level dimensions for:

* target population / eligibility
* screening
* consent / enrollment

These are core components of participant recruitment but are distributed indirectly across other branches.

### Character

**Thematic and technology/policy-oriented rather than structurally decompositional.**

### Preliminary assessment

The vertical outputs are generally strong once a parent has been selected, but the **horizontal decomposition is the weakest of the three models** in this run.

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

This captures a scientifically and operationally important part of clinical recruitment that neither Luna nor DeepSeek isolates as clearly.

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

### Preliminary assessment

Gemini produces the strongest overall hierarchy in this particular run.

---

# Preliminary Ranking

Based strictly on this behavioral sample:

## 1. Gemini 2.5 Flash

Best overall structural decomposition.

Strengths:

* clear fundamental dimensions
* explicit screening/enrollment pathway
* strong vertical parent-child relationships
* consistent granularity
* good functional separation

## 2. GPT-5.6 Luna

Very close to Gemini and stronger than the earlier GPT-5 mini result.

Strengths:

* disciplined horizontal decomposition
* strong vertical consistency
* concise, operational categorization
* little obvious semantic drift

Primary weakness:

* some compound branches such as `Recruitment Performance and Equity`
* recruitment and retention concepts occasionally blend

## 3. DeepSeek Chat

Produces strong individual thoughts but the weakest horizontal ontology.

Primary weaknesses:

* promotes cross-cutting themes to top-level dimensions
* lacks explicit eligibility and screening/enrollment branches
* mixes fundamental structure with technology and policy themes

---

# Key Finding

All three models successfully understand the basic Array of Thoughts instruction:

```text
horizontal = peer-level decomposition
vertical = more-specific decomposition beneath a selected parent
```

The main difference is **not whether the models can generate relevant thoughts**.

The important difference is:

> **How well does each model identify the fundamental structure of the concept?**

That appears to be the more discriminating evaluation criterion.

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

This historical run provides encouraging evidence that `bot0-thought-graph` can produce useful provider-independent hierarchical decomposition.

The preliminary ordering is:

```text
Gemini 2.5 Flash
≈ GPT-5.6 Luna
> DeepSeek Chat
```

The difference between Gemini and Luna is relatively small and should not yet be treated as conclusive.

The DeepSeek result shows a more meaningful structural weakness, but this run should not be considered the final DeepSeek comparison because it used:

```text
deepseek-chat
```

rather than the current V4 Flash benchmark model:

```text
deepseek-v4-flash
```

The next controlled comparison should therefore use the same concept and generation settings with both DeepSeek V4 Flash modes:

```text
GPT-5.6 Luna
Gemini 3.6 Flash
DeepSeek V4 Flash (non-thinking)
DeepSeek V4 Flash (thinking)
```

and ideally repeat each model several times before drawing a final provider-level conclusion.
