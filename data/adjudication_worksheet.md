# Scorer change — adjudication worksheet

One entry per dimension whose score or fallback flag moved between the committed snapshot (legacy per-dimension scorer) and the combined single-call scorer.

**How to use this (the criterion is this process, not a number):** for each entry, read the rubric, read the cited evidence on both sides, and tick a winner — the score the rubric + evidence better support. The maintainer owns the accept/reject decision and any rule over these marks (e.g. how many combined-wins-or-ties are required, and how to treat statements whose overall moved > 0.2). This tool does not assert that rule.

Changed dimensions: **13**

| statement | dimension | old | new | Δ | fallback | winner |
|---|---|---|---|---|---|---|
| tesco_2024 | 2 Policies | 3 | 2 | -1 | False→False | |
| tesco_2025 | 1 Structure and supply chains | 2 | 3 | +1 | False→False | |
| tesco_2025 | 4 Risk assessment | 4 | 3 | -1 | False→False | |
| barclays_2023 | 1 Structure and supply chains | 3 | 2 | -1 | False→False | |
| barclays_2024 | 6 Training | 3 | 4 | +1 | False→False | |
| damen_2022 | 4 Risk assessment | 2 | 1 | -1 | False→False | |
| damen_2022 | 5 Effectiveness and KPIs | 2 | 1 | -1 | False→False | |
| siemens-gamesa_2022 | 2 Policies | 3 | 2 | -1 | False→False | |
| dell_2022 | 1 Structure and supply chains | 3 | 2 | -1 | False→False | |
| dell_2023 | 1 Structure and supply chains | 4 | 3 | -1 | False→False | |
| dell_2023 | 4 Risk assessment | 3 | 4 | +1 | False→False | |
| hiscox_2022 | 5 Effectiveness and KPIs | 2 | 3 | +1 | False→False | |
| hiscox_2022 | 6 Training | 3 | 2 | -1 | False→False | |

---

### tesco_2024 — Dimension 2: Policies (UK MSA s.54(5)(b))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Are policies named, dated, and tied to modern slavery specifically, or is there only generic CSR / code-of-conduct language?

**LEGACY (committed snapshot): score = 3**
- justification: The statement names specific policies (Code of Business Conduct, Human Rights Policy, Employer Pays Principle) tied directly to modern slavery/labour rights, and describes a concrete mechanism—expanding a supplier policy requirement to non-food UK/ROI sites and mandating alignment with the Employer Pays Principle. However, there is no measurable evidence of outcomes (e.g., compliance rates, audit results) tied to these policies, so it falls short of a 4.
- evidence:
    - 'Our human rights approach, including tackling modern slavery, is supported by our Code of Business Conduct and Human Rights Policy which set out our obligations to customers, colleagues and communities in our own operations and supply chains'
    - 'It is a policy requirement that all suppliers of food, non-food, and goods and services not for resale into Tesco UK align with the Employer Pays Principle'
    - 'In 2021, we expanded this requirement to all non-food sites supplying into the UK and ROI'

**COMBINED (new): score = 2**
- justification: Named policies (Code of Business Conduct, Human Rights Policy, Human Rights Blueprint, Employer Pays Principle) are tied to modern slavery, but there is little detail on dates or specific policy content, keeping this at a general-commitment level.
- evidence:
    - 'Our human rights approach, including tackling modern slavery, is supported by our Code of Business Conduct and Human Rights Policy which set out our obligations to customers, colleagues and communities in our own operations and supply chains'
    - 'It is a policy requirement that all suppliers of food, non-food, and goods and services not for resale into Tesco UK align with the Employer Pays Principle'
    - 'Continue rollout of Human Rights Blueprint'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Attribution:** ☐ thinking-off artifact  ☑ structural to combining  ☐ borderline-unstable  (snapshot=3, disabled=2, adaptive=2) — adaptive keeps the combined score — thinking does NOT recover it; adjudicate
**Notes:** 

---

### tesco_2025 — Dimension 1: Structure and supply chains (UK MSA s.54(5)(a))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Does the statement describe the organisation's structure, business, and supply chains with specificity — named tiers, geographies, and product/service categories — rather than generic descriptions?

**LEGACY (committed snapshot): score = 2**
- justification: The statement provides general descriptions of Tesco's operations (store counts, employee numbers, geographic footprint) and names some sourcing regions and risk categories, but lacks specific tier-level supplier mapping, named suppliers, or quantified supply chain data. Most claims are generic descriptions rather than concrete mechanisms; only forward-looking commitments (e.g., expanding monitoring to tier 2/3) suggest lower-tier visibility is still a gap, not an achieved specificity.
- evidence:
    - 'We have thousands of direct and indirect suppliers who grow, make and move raw materials and finished products across our global supply chain. These suppliers range from large agriculture businesses to smallholders and manufacturing companies'
    - 'We target action in our key sourcing regions including China and Southeast Asia, Indian Subcontinent, Europe, Middle East, and Africa, with key focuses on Bangladesh, China, India, Sri Lanka, Thailand, Turkey and the UK'
    - 'Our due diligence has identified a greater risk of modern slavery in the lower tiers of our supply chain'
    - 'Tesco is one of the world’s leading multinational retailers. Our largest operations are in the UK, where we have close to 3,800 stores. We also have businesses in the Republic of Ireland, Czech Republic, Hungary and Slovakia'

**COMBINED (new): score = 3**
- justification: The statement names specific tiers, geographies (Thailand, Malaysia, Bangladesh, India, Sri Lanka, Turkey, UK, China, Southeast Asia), and product categories (fish/seafood, home and clothing, distribution) and identifies lower-tier risk, but the structural description of the business itself remains fairly generic and there is limited quantification of supply chain scale (e.g., no total supplier counts across most categories).
- evidence:
    - 'We target action in our key sourcing regions including China and Southeast Asia, Indian Subcontinent, Europe, Middle East, and Africa, with key focuses on Bangladesh, China, India, Sri Lanka, Thailand, Turkey and the UK'
    - 'Our due diligence has identified a greater risk of modern slavery in the lower tiers of our supply chain'
    - 'Our current modern slavery strategy focuses on the following salient risk areas within both our own operations and supply chains: • Higher risk labour in our own operations, such as third-party service providers • UK Distribution • Thailand and Malaysia • Fish and Seafood • Home and clothing • UK seasonal workers'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Notes:** 

---

### tesco_2025 — Dimension 4: Risk assessment (UK MSA s.54(5)(d))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Does the statement name specific high-risk geographies, sectors, or supply-chain stages, versus a generic acknowledgement that risk exists?

**LEGACY (committed snapshot): score = 4**
- justification: The statement describes concrete mechanisms for risk assessment (FNET risk ratings, ILO root-cause framework, regional human rights specialists) and names specific high-risk contexts such as the Seasonal Worker Scheme and shipping/vessel sourcing, going well beyond a generic acknowledgement. It also provides a measurable outcome: mandatory independent audits for Tier 1 sites in high-risk countries, quantified as 28% of total Tier 1 suppliers.
- evidence:
    - 'We use the Food Network for Ethical Trade (FNET) risk ratings to inform this, combined with our own understanding of labour rights and modern slavery risks in our key sourcing sectors'
    - 'In high-risk countries, Tier 1 sites are required to have an independent human rights audit from a Tesco approved auditor before they start supplying to Tesco, and then on an annual basis. This represents around 28% of our total Tier 1 suppliers'
    - 'The well-documented risks within the Seasonal Worker Scheme remain a priority in our modern slavery approach'
    - 'Relative lack of traceability and visibility of issues in the sector • Difficulty in replicating or adapting certain due diligence practices or techniques, including audits, particularly with regards to vessels'
    - 'Difficulty in replicating or adapting certain due diligence practices or techniques, including audits, particularly with regards to vessels'

**COMBINED (new): score = 3**
- justification: Concrete mechanisms for risk assessment are described, including use of FNET risk ratings, country/sector/labour-type analysis, and specific high-risk sector challenges (fishing, seasonal workers), but this dimension's own claims lack strong measurable outcomes tied directly to risk assessment methodology itself.
- evidence:
    - 'We assess the potential modern slavery risks within our own operations and supply chain by considering the country of origin of the products, raw materials or services we source, as well as the human rights trends of each sector. We also consider the type of labour being used, whether skilled, semi-skilled or un-skilled, and whether seasonal, permanent, agency or migrant labour'
    - 'We use the Food Network for Ethical Trade (FNET) risk ratings to inform this, combined with our own understanding of labour rights and modern slavery risks in our key sourcing sectors'
    - 'In high-risk countries, Tier 1 sites are required to have an independent human rights audit from a Tesco approved auditor before they start supplying to Tesco, and then on an annual basis. This represents around 28% of our total Tier 1 suppliers'
    - 'Our approach to preventing, identifying, and mitigating modern slavery is based on the leading factors which are acknowledged by the ILO as root causes of modern slavery in supply chains, such as: • Recruitment fees (leading to debt bondage) • Cultural isolation • Restricted movement • Working conditions'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Attribution:** ☐ thinking-off artifact  ☑ structural to combining  ☐ borderline-unstable  (snapshot=4, disabled=3, adaptive=3) — adaptive keeps the combined score — thinking does NOT recover it; adjudicate
**Notes:** 

---

### barclays_2023 — Dimension 1: Structure and supply chains (UK MSA s.54(5)(a))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Does the statement describe the organisation's structure, business, and supply chains with specificity — named tiers, geographies, and product/service categories — rather than generic descriptions?

**LEGACY (committed snapshot): score = 3**
- justification: The statement provides specific structural details (divisions, employee headcount, physical presence in 25 countries, geographic concentration of spend) and names first-tier supplier categories, going beyond generic description. However, it lacks disclosure of deeper supply chain tiers (tier 2+) or specific geographies/products within those categories, and there is no measurable outcome tied to supply chain mapping itself, only descriptive metrics.
- evidence:
    - 'Barclays Bank PLC has a physical presence in 25 countriesc, with its registered office in London, UK'
    - 'Though our businesses are geographically diverse, more than 90% of our third-party spend is concentrated in the UK and US, our two home markets'
    - 'Those with whom we contract directly, also known as first-tier suppliers, generally fall into one or more of the following categories: Corporate Real Estate and related services, Technology Infrastructure, Software & Services, Banking Operations, Professional Services, Marketing and Human Resources'

**COMBINED (new): score = 2**
- justification: The statement provides some specific figures on employee counts, country presence, and spend concentration, plus named first-tier supplier categories, but lacks detail on deeper supply chain tiers or geographies beyond top-line figures.
- evidence:
    - 'Though our businesses are geographically diverse, more than 90% of our third-party spend is concentrated in the UK and US, our two home markets'
    - 'Those with whom we contract directly, also known as first-tier suppliers, generally fall into one or more of the following categories: Corporate Real Estate and related services, Technology Infrastructure, Software & Services, Banking Operations, Professional Services, Marketing and Human Resources'
    - 'Barclays Bank PLC has a physical presence in 25 countriesc, with its registered office in London, UK'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Attribution:** ☐ thinking-off artifact  ☑ structural to combining  ☐ borderline-unstable  (snapshot=3, disabled=2, adaptive=2) — adaptive keeps the combined score — thinking does NOT recover it; adjudicate
**Notes:** 

---

### barclays_2024 — Dimension 6: Training (UK MSA s.54(5)(f))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Does it say who is trained, how often, and whether completion is tracked — versus a bare mention that training exists?

**LEGACY (committed snapshot): score = 3**
- justification: The statement identifies specific audiences (all employees for financial crime training, Procurement/Events/Corporate Real Estate colleagues for a dedicated modern slavery eLearning module) and frequency (annual, refreshed annually), plus additional targeted sessions for Accountable Executives and cross-business forums. This goes beyond a bare mention to describe concrete mechanisms, but there is no completion-tracking data, participation rates, or measurable outcomes reported, so it falls short of a 4.
- evidence:
    - 'All employees undertake mandatory financial crime training, which is refreshed annually and includes content related to modern slavery'
    - 'All Procurement, Events & Hospitality and Corporate Real Estate colleagues globally must annually complete a dedicated eLearning module focusing on the UK and Australian Modern Slavery Acts and steps employees should take to seek to identify and mitigate modern slavery and human trafficking risks within our supply chain'
    - 'Delivered modern slavery training and awareness raising session for Anti-Slavery Day, to Accountable Executives who own relationships with TPSPs in sectors with an inherent risk of modern slavery'

**COMBINED (new): score = 4**
- justification: Training disclosures specify who is trained (Procurement, Events & Hospitality, Corporate Real Estate colleagues, Accountable Executives, all employees via financial crime training), frequency (annual refresh), and completion tracking, supported by a measurable completion rate metric.
- evidence:
    - 'All Procurement, Events & Hospitality and Corporate Real Estate colleagues globally must annually complete a dedicated eLearning module focusing on the UK and Australian Modern Slavery Acts and steps employees should take to seek to identify and mitigate modern slavery and human trafficking risks within our supply chain'
    - 'All employees undertake mandatory financial crime training, which is refreshed annually and includes content related to modern slavery'
    - 'Percentage of assigned colleagues in Sourcing, Corporate Real Estate Services and Events and Hospitality functions completing modern slavery training22 99'
    - 'Delivered modern slavery training and awareness raising session for Anti-Slavery Day, to Accountable Executives who own relationships with TPSPs in sectors with an inherent risk of modern slavery'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Notes:** 

---

### damen_2022 — Dimension 4: Risk assessment (UK MSA s.54(5)(d))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Does the statement name specific high-risk geographies, sectors, or supply-chain stages, versus a generic acknowledgement that risk exists?

**LEGACY (committed snapshot): score = 2**
- justification: The statement references a general risk assessment process tied to business partner due diligence and a commitment to escalate identified cases, but it never names specific high-risk geographies, sectors, or supply-chain stages, nor does it describe how risk is actually measured or prioritized.
- evidence:
    - 'The Compliance department is closely involved in the business partners due diligence process and supports the risk assessment process related to modern slavery'
    - 'To maintain our zero tolerance policy towards slavery and human trafficking, senior management will be involved in case of identified potential cases of modern slavery and human trafficking to take corrective action'

**COMBINED (new): score = 1**
- justification: The statement mentions that a risk assessment process exists and that senior management is involved in corrective action, but does not name specific high-risk geographies, sectors, or supply chain stages.
- evidence:
    - 'The Compliance department is closely involved in the business partners due diligence process and supports the risk assessment process related to modern slavery'
    - 'To maintain our zero tolerance policy towards slavery and human trafficking, senior management will be involved in case of identified potential cases of modern slavery and human trafficking to take corrective action'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Attribution:** ☐ thinking-off artifact  ☑ structural to combining  ☐ borderline-unstable  (snapshot=2, disabled=1, adaptive=1) — adaptive keeps the combined score — thinking does NOT recover it; adjudicate
**Notes:** 

---

### damen_2022 — Dimension 5: Effectiveness and KPIs (UK MSA s.54(5)(e))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Are there measurable indicators with numbers or targets, versus aspirational statements with no way to measure progress?

**LEGACY (committed snapshot): score = 2**
- justification: The statement claims to use KPIs related to training, auditing, and supplier upskilling, but no actual numbers, targets, or measured outcomes are disclosed—only a generic assertion that such indicators exist without specifying mechanisms or results.
- evidence:
    - 'In order to assess the effectiveness of the measures taken to ensure adherence to this Damen Shipyards Group Modern Slavery Statement, we make use of key performance indicators related to training and awareness; supply chain auditing and verification, and steps taken to upskill our high risk suppliers, and assessing their ability to detect and mitigate modern slavery risk in supply chain'

**COMBINED (new): score = 1**
- justification: The statement mentions using KPIs related to training, auditing, and supplier upskilling to assess effectiveness, but no actual figures, targets, or results are disclosed.
- evidence:
    - 'In order to assess the effectiveness of the measures taken to ensure adherence to this Damen Shipyards Group Modern Slavery Statement, we make use of key performance indicators related to training and awareness; supply chain auditing and verification, and steps taken to upskill our high risk suppliers, and assessing their ability to detect and mitigate modern slavery risk in supply chain'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Attribution:** ☐ thinking-off artifact  ☑ structural to combining  ☐ borderline-unstable  (snapshot=2, disabled=1, adaptive=1) — adaptive keeps the combined score — thinking does NOT recover it; adjudicate
**Notes:** 

---

### siemens-gamesa_2022 — Dimension 2: Policies (UK MSA s.54(5)(b))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Are policies named, dated, and tied to modern slavery specifically, or is there only generic CSR / code-of-conduct language?

**LEGACY (committed snapshot): score = 3**
- justification: The statement names specific, dated policies (SGRE Business Conduct Guidelines, Code of Conduct for Suppliers, financial year 2022) explicitly tied to anti-slavery principles referencing ILO conventions, and describes a concrete mechanism—mandatory employee sign-off on the Guidelines during recruitment. However, there is no measurable evidence such as completion rates, audit results, or numbers of employees signing, preventing a score of 4.
- evidence:
    - 'Each employee is required to sign a statement that they have read and understood the Business Conduct Guidelines as part of our recruitment process'
    - 'SGRE is a member of the United Nations Global Compact and our Business Conduct Guidelines require that our employees recognise and apply globally-relevant anti-slavery principles, including the International Labour Organisation’s Tripartite Declaration of Principles, and its Declaration on Fundamental Principles and Rights at Work, in particular with respect to the elimination of child labour, abolition of forced labour, prohibition of discrimination, and rights to freedom of association and collective bargaining'
    - 'During financial year ending on 30th September 2022, the Company has continued to follow the Siemens Gamesa Renewable Energy S.A. (“SGRE”) global guidelines and codes of conduct, including the SGRE Business Conduct Guidelines and the SGRE Code of Conduct for Suppliers and Third Party Intermediaries'

**COMBINED (new): score = 2**
- justification: Policies are named (Business Conduct Guidelines, Code of Conduct for Suppliers) and tied to broader ethical/anti-slavery principles referencing ILO standards, but they remain general corporate governance policies rather than modern-slavery-specific instruments, and there is a mechanism (signed acknowledgment) supporting rollout but no measurement.
- evidence:
    - 'SGRE is a member of the United Nations Global Compact and our Business Conduct Guidelines require that our employees recognise and apply globally-relevant anti-slavery principles, including the International Labour Organisation’s Tripartite Declaration of Principles, and its Declaration on Fundamental Principles and Rights at Work, in particular with respect to the elimination of child labour, abolition of forced labour, prohibition of discrimination, and rights to freedom of association and collective bargaining'
    - 'Each employee is required to sign a statement that they have read and understood the Business Conduct Guidelines as part of our recruitment process'
    - 'During financial year ending on 30th September 2022, the Company has continued to follow the Siemens Gamesa Renewable Energy S.A. (“SGRE”) global guidelines and codes of conduct, including the SGRE Business Conduct Guidelines and the SGRE Code of Conduct for Suppliers and Third Party Intermediaries'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Attribution:** ☑ thinking-off artifact  ☐ structural to combining  ☐ borderline-unstable  (snapshot=3, disabled=2, adaptive=3) — reverts to the snapshot score under adaptive thinking — re-enabling thinking recovers it
**Notes:** 

---

### dell_2022 — Dimension 1: Structure and supply chains (UK MSA s.54(5)(a))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Does the statement describe the organisation's structure, business, and supply chains with specificity — named tiers, geographies, and product/service categories — rather than generic descriptions?

**LEGACY (committed snapshot): score = 3**
- justification: The statement goes beyond generic description by disclosing a Public Supplier List covering at least 95% of direct material spend, naming supplier tiers (ODMs, final assembly), and providing employee headcount, which is a concrete mechanism for supply chain mapping. However, it lacks specific named geographies or product/service category breakdowns and no outcome/impact metrics tied to this mapping are provided, so it falls short of a 4.
- evidence:
    - 'Dell’s Public Supplier List includes original design manufacturers (ODMs), final assembly and suppliers that Dell buys from directly and/or provide substantial product transformation, including the location of these facilities. This list represents a snapshot covering at least 95% of Dell’s direct material spend during fiscal year 2022'
    - 'Dell directly employs approximately 130,000 people worldwide'
    - 'In addition to these direct global material suppliers, our next biggest areas of spend include products and services procured in country or regionally for customer-facing services, marketing and global real estate and facilities'

**COMBINED (new): score = 2**
- justification: The statement gives generic descriptions of Dell's business and headcount, plus a Public Supplier List covering 95% of direct material spend with facility locations, but lacks specific named tiers, geographies, or product/service category breakdowns within the statement itself.
- evidence:
    - 'Dell’s Public Supplier List includes original design manufacturers (ODMs), final assembly and suppliers that Dell buys from directly and/or provide substantial product transformation, including the location of these facilities. This list represents a snapshot covering at least 95% of Dell’s direct material spend during fiscal year 2022'
    - 'Dell directly employs approximately 130,000 people worldwide'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Attribution:** ☐ thinking-off artifact  ☑ structural to combining  ☐ borderline-unstable  (snapshot=3, disabled=2, adaptive=2) — adaptive keeps the combined score — thinking does NOT recover it; adjudicate
**Notes:** 

---

### dell_2023 — Dimension 1: Structure and supply chains (UK MSA s.54(5)(a))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Does the statement describe the organisation's structure, business, and supply chains with specificity — named tiers, geographies, and product/service categories — rather than generic descriptions?

**LEGACY (committed snapshot): score = 4**
- justification: The statement goes beyond generic descriptions by naming specific manufacturing geographies, component sourcing countries, and describing a Public Supplier List mechanism covering ODMs and final assembly suppliers with a measurable coverage figure (95% of direct material spend), providing concrete and quantified supply chain specificity.
- evidence:
    - 'Our own manufacturing facilities are located in the United States, Malaysia, China, Brazil, India, Poland, and Ireland. We also use contract manufacturers throughout the world to manufacture or assemble our products under the Dell Technologies brand. Components used in these manufacturing facilities are sourced primarily from the same locations listed above, and from Japan, South Korea, Mexico, Taiwan, Singapore, Philippines, Thailand, Laos, Germany, Netherlands, Israel, Vietnam, and Indonesia'
    - 'Dell’s Public Supplier List identifies the category type and location of our original design manufacturers (ODMs) and final assembly Suppliers. This list represents a snapshot covering at least 95% of Dell’s direct material spend during fiscal year 2022'
    - 'We have operations and conduct business in the Americas, Europe, the Middle East, Asia, and other geographic regions. As reported in our most recent 10K, Dell employs approximately 133,000 people worldwide'
    - 'As reported in our most recent 10K, Dell employs approximately 133,000 people worldwide'

**COMBINED (new): score = 3**
- justification: The statement names specific manufacturing geographies, contract manufacturer use, and component sourcing countries, plus a Public Supplier List covering 95% of direct material spend, giving concrete structural detail. However, it lacks named tier-1/tier-2 supplier names or product-category breakdowns, so measurable outcomes are absent.
- evidence:
    - 'Our own manufacturing facilities are located in the United States, Malaysia, China, Brazil, India, Poland, and Ireland. We also use contract manufacturers throughout the world to manufacture or assemble our products under the Dell Technologies brand. Components used in these manufacturing facilities are sourced primarily from the same locations listed above, and from Japan, South Korea, Mexico, Taiwan, Singapore, Philippines, Thailand, Laos, Germany, Netherlands, Israel, Vietnam, and Indonesia'
    - 'Dell’s Public Supplier List identifies the category type and location of our original design manufacturers (ODMs) and final assembly Suppliers. This list represents a snapshot covering at least 95% of Dell’s direct material spend during fiscal year 2022'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Attribution:** ☐ thinking-off artifact  ☑ structural to combining  ☐ borderline-unstable  (snapshot=4, disabled=3, adaptive=3) — adaptive keeps the combined score — thinking does NOT recover it; adjudicate
**Notes:** 

---

### dell_2023 — Dimension 4: Risk assessment (UK MSA s.54(5)(d))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Does the statement name specific high-risk geographies, sectors, or supply-chain stages, versus a generic acknowledgement that risk exists?

**LEGACY (committed snapshot): score = 3**
- justification: The statement goes beyond generic acknowledgement by describing a concrete mechanism: an annual, data-driven country risk scoring system that incorporates internal audit data, NGO information, and sources like the Trafficking in Persons Report and Global Slavery Index, which is used to target audits toward higher-risk locations (e.g., contrasting with lower-risk Western Europe, USA, Australia) and higher-risk worker categories like foreign migrant workers (FMWs). However, no specific high-risk countries or measurable outcomes (e.g., number of high-risk suppliers identified, specific risk scores) are disclosed, so it falls short of a 4.
- evidence:
    - "Dell's risk assessment method incorporates the resources of Dell’s internal audit activity, international governments, and NGO information to assign each country a risk score which is heavily weighted by forced labor risks, including for FMWs"
    - 'For locations that are lower risk and for which we have not seen high risk in their in-country or regional supply chains, such as Western Europe, USA or Australia, we do not divert resources from higher risk locations'
    - 'This risk assessment incorporates data on human trafficking incidence from sources including, but not limited to, the U.S. State Department\'s annual "Trafficking in Persons Report”, The Global Slavery Index, and the U.S. Department of Labor’s Bureau of International Labor Affairs'
    - 'The risk assessment is completed annually'
    - 'For example, Dell has encountered, investigated, and mitigated risks to FMWs in situations involving Onsite Service Providers (OSPs) and in locations where worker fees might be culturally accepted'
    - 'The risk scores inform our audit programs, such that we focus resources in locations where we have seen higher risk'

**COMBINED (new): score = 4**
- justification: Dell identifies foreign migrant workers and specific supplier types/geographies as highest risk, uses an annual country risk-scoring methodology incorporating named external data sources (Trafficking in Persons Report, Global Slavery Index, DOL ILAB), and ties this scoring to differentiated audit resource allocation, demonstrating concrete mechanism-based risk assessment.
- evidence:
    - "Dell's risk assessment method incorporates the resources of Dell’s internal audit activity, international governments, and NGO information to assign each country a risk score which is heavily weighted by forced labor risks, including for FMWs"
    - 'This risk assessment incorporates data on human trafficking incidence from sources including, but not limited to, the U.S. State Department\'s annual "Trafficking in Persons Report”, The Global Slavery Index, and the U.S. Department of Labor’s Bureau of International Labor Affairs'
    - 'The risk scores inform our audit programs, such that we focus resources in locations where we have seen higher risk'
    - 'The risk assessment is completed annually'
    - 'For example, Dell has encountered, investigated, and mitigated risks to FMWs in situations involving Onsite Service Providers (OSPs) and in locations where worker fees might be culturally accepted'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Notes:** 

---

### hiscox_2022 — Dimension 5: Effectiveness and KPIs (UK MSA s.54(5)(e))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Are there measurable indicators with numbers or targets, versus aspirational statements with no way to measure progress?

**LEGACY (committed snapshot): score = 2**
- justification: The single claim reports a whistleblowing outcome (zero reported cases) but this is a negative/absence metric rather than evidence of active measurement of effectiveness, and no mechanisms, targets, or KPIs for tracking progress are described. This falls short of demonstrating concrete mechanisms with measurement, resembling a general monitoring commitment more than a substantiated KPI framework.
- evidence:
    - 'In 2021 there were no suspected cases of Modern Slavery reported through the Whistleblowing channel, however we remain diligent in monitoring our business and suppliers to ensure slavery and human trafficking do not feature in our business or supply chain'

**COMBINED (new): score = 3**
- justification: A measurable indicator is provided (zero suspected cases reported via whistleblowing in 2021), giving some quantifiable evidence, though it is a single narrow metric without broader KPI targets or trend data.
- evidence:
    - 'In 2021 there were no suspected cases of Modern Slavery reported through the Whistleblowing channel, however we remain diligent in monitoring our business and suppliers to ensure slavery and human trafficking do not feature in our business or supply chain'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Notes:** 

---

### hiscox_2022 — Dimension 6: Training (UK MSA s.54(5)(f))

**Rubric (0–4):**

| score | meaning |
|---|---|
| 0 | Not addressed. |
| 1 | Mentioned, no substance. |
| 2 | General commitments, no mechanisms. |
| 3 | Concrete mechanisms described, weak or no measurement. |
| 4 | Concrete mechanisms plus measurable evidence or outcomes. |

Dimension question: Does it say who is trained, how often, and whether completion is tracked — versus a bare mention that training exists?

**LEGACY (committed snapshot): score = 3**
- justification: The statement specifies who is trained (all employees) and how often (annually) and identifies content (raising concerns), which constitutes a concrete mechanism. However, there is no measurable evidence of completion rates, tracking systems, or outcomes, preventing a score of 4.
- evidence:
    - 'All our employees undertake annual mandatory regulatory training which includes specific content on raising concerns within the business'

**COMBINED (new): score = 2**
- justification: Training is mandatory and annual for all employees, but the statement does not specify modern-slavery-specific content depth, completion tracking, or metrics on training uptake.
- evidence:
    - 'All our employees undertake annual mandatory regulatory training which includes specific content on raising concerns within the business'

**WINNER (human):** ☐ legacy  ☐ combined  ☐ neither / re-score
**Attribution:** ☐ thinking-off artifact  ☑ structural to combining  ☐ borderline-unstable  (snapshot=3, disabled=2, adaptive=2) — adaptive keeps the combined score — thinking does NOT recover it; adjudicate
**Notes:** 

---
