# Models in plain text

One section per model card, in pipeline order. Text is generated from `analysis/outputs/cards/*.json`.

## 1. Preparing the breach records (`data-preparation`)

Module: 1: Descriptive statistics and data preparation. Stage: prepare. Runs live on the user's business: no.

**Question.** Which incident records can we trust and use, and in what form, to learn how breaches happen?

**Why this model.** Records lost is extremely right skewed (skewness 50.6): the mean is 22,774,208 while the median is 1,364, so a few mega breaches dominate any raw average. After log10(1 + x) the skewness falls to 0.36, which makes regression and distance based methods usable. Dropping every row with any gap would remove 98% of incidents, so Unknown is kept as a category and only each model's own inputs must be present.

**Result.**

- raw files: 10596
- flattened rows: 10596
- columns: 55
- classifier rows: 8267
- breach yes: 7492
- breach no: 775
- regression rows: 5398
- skew raw: 50.57

**What it yields.** Out of 10596 public incident reports, 8267 clearly say whether data was exposed and 5398 say how many records were lost. CyCRS learns how breaches happen from these rows and measures breach size on a log scale so one giant leak does not distort the picture for a small business.

**Limitations.** Only 775 incidents (9.4%) are No, so the breach classifier still has far fewer negatives than positives. 688 incidents have no confidentiality section and are counted as no disclosure; this assumes the coder would have recorded any data exposure. VCDB is built from public news reports, so large and US organisations are over represented. VERIS Small (up to 1000 staff) cannot be split and is counted as small. Discovery time in days is known for only 1436 incidents.

## 2. What the incident records look like (`descriptive`)

Module: 2: Descriptive statistics and probability. Stage: explore. Runs live on the user's business: no.

**Question.** How big are typical breaches, how long do they go unnoticed, and which attacks and attackers are most common?

**Why this model.** Records lost has mean 22,774,208 but median 1,364 and skewness 50.6, so medians, IQRs and log-scale histograms describe it better than means. Action category and actor type are nominal, so counts are shown as bars and shares as a pie (external actors are 55% of incidents). Discovery time and records lost are both skewed ratio variables, so their link is shown on log axes and measured with Spearman rho (-0.04), which does not assume normality.

**Result.**

- incidents: 10596
- median records lost: 1364
- median discovery days: 91.31
- spearman discovery records: -0.03517

**What it yields.** A typical breach in the data exposes about 1,364 records and goes unnoticed for about 91 days, while a few huge breaches pull the average up to 22,774,208. Hacking is the most common kind of attack and outsiders cause most incidents, so CyCRS starts its threat list there.

**Limitations.** VCDB comes from public reports, so large organisations and the USA are over represented. Discovery time is known for only 1436 incidents. Employee count is banded, so its mean and SD are on band codes, not people.

## 3. Which curve fits breach size (`distribution-fit`)

Module: 2: Probability distributions. Stage: explore. Runs live on the user's business: no.

**Question.** Is the number of records lost in a breach closer to a normal or a lognormal distribution?

**Why this model.** Records lost is strictly positive with skewness 50.6, the typical shape of a lognormal variable, while a normal curve allows negative values and is symmetric. The Kolmogorov-Smirnov distance is 0.486 for the normal fit and 0.091 for the lognormal fit, so the lognormal curve is much closer to the data.

**Result.**

- n: 5398
- skew records lost: 50.57
- ks d normal: 0.4858
- ks d lognormal: 0.0914
- lognormal sigma: 5.032
- lognormal scale: 1329

**What it yields.** Breach sizes follow a lognormal pattern far better than a bell curve (distance 0.091 vs 0.486). That is why every later model of breach size in CyCRS works on the log of records lost and converts back to records and rupees at the end.

**Limitations.** KS p-values are optimistic because parameters were estimated from the same data. Even the lognormal fit is rejected at this sample size; it is an approximation, not an exact law.

## 4. Attack chances by sector (`conditional-probability`)

Module: 2: Probability. Stage: explore. Runs live on the user's business: yes.

**Question.** Given a business's sector, what share of past incidents involved each kind of attack?

**Why this model.** Sector and action category are both categorical, so the simplest honest estimate of P(action | sector) is the observed share within each sector. Every top sector has at least 271 incidents, enough for stable shares, and the chi-square test finds attack mix depends on sector (Cramer's V 0.25).

**Result.**

- n Health Care and Social Assistance: 2564
- n Public Administration: 2403
- n Educational Services: 1155
- n Finance and Insurance: 980
- n Information: 876
- n Retail Trade: 529
- n Professional, Scientific, and Technical Services: 488
- n Manufacturing: 271

**What it yields.** In Health Care and Social Assistance, 27% of past incidents involved physical, and each sector has its own leading threat. CyCRS shows these shares as the simple baseline for a user's sector, and its attack likelihood model must do better than this table to be used.

**Limitations.** An incident can have several action categories, so a sector's shares can add up to more than 1. Shares describe reported incidents, not the chance that a given business is attacked.

## 5. Testing what really differs (`hypothesis-tests`)

Module: 2: Hypothesis testing. Stage: explore. Runs live on the user's business: no.

**Question.** Which differences in attack type, breach size, detection time and regional crime are real rather than chance?

**Why this model.** Normality checks fail for breach size (internal p 2.1e-42) and for log discovery time (p 3.6e-15), so rank-based tests (Mann-Whitney, Kruskal-Wallis) are primary. Attack type, size and sector are categorical, so association is tested with chi-square and sized with Cramer's V, and ransomware share is a proportion, so a two-proportion z-test fits. Running 9 tests raises the chance of a false alarm, so Holm-adjusted p-values decide.

**Result.**

- tests: 9
- rejected holm: 7
- ransomware share 2020 on: 0.5517
- ransomware share before 2020: 0.02438

**What it yields.** 7 of 9 tested differences hold up after correcting for multiple tests: attack mix by business size, attack mix by sector, breach size by insider or outsider, detection time by sector (ANOVA), the rise in ransomware share, the ransomware rise without 2023, crime type mix by Indian region, while detection time by sector (Kruskal-Wallis), crime rate by Indian region could be chance. CyCRS uses only the differences that survive as inputs for tailoring its advice, and shows the effect size so a statistically real but tiny difference is not oversold.

**Limitations.** VCDB is not a random sample of businesses, so tests describe reported incidents. With thousands of incidents even negligible differences can be significant; read the effect size. The five-region grouping of states is a CyCRS choice and affects the regional tests. 857 incidents are dated 2023 and 91% of them involve ransomware; without them the share from 2020 is 22.1% instead of 55.2% (robustness row), so part of the rise is a collection effect.

## 6. Does a bigger organisation lose more records? (`slr`)

Module: 3: Simple linear regression. Stage: explore. Runs live on the user's business: no.

**Question.** How much does the size of an organisation alone explain how many records it loses in a breach?

**Why this model.** Both variables are on log scales, where breach size is close to symmetric (skewness 0.36), so a straight line is a fair first model. A single predictor shows how much size alone explains before adding attack details; here R2 is 0.117.

**Result.**

- intercept: 4.906
- skew log records: 0.3601
- slope: -0.528
- r2: 0.1172
- p value: 0
- n: 3693

**What it yields.** Each tenfold increase in staff cuts expected records lost to about 30% (larger organisations in VCDB tend to lose fewer records), but size alone explains only 11.7% of the variation. So CyCRS does not judge breach size from company size alone; it adds sector and attack type in the multiple model.

**Limitations.** Employee count is banded, so x takes only eight values. Large organisations dominate VCDB.

## 7. How big a breach could be (`mlr-impact`)

Module: 3: Multiple linear regression. Stage: impact. Runs live on the user's business: yes.

**Question.** Given a business's sector, size and the type of attack, how many records would a breach be expected to expose?

**Why this model.** Records lost has skewness 50.6 and a lognormal curve fits it far better than a normal one (KS D 0.091 vs 0.486), so the target is log10(1 + records). On that scale effects are multiplicative and OLS gives coefficients a business owner can read as 'this attack multiplies expected records lost by 10 to the power b'. Breusch-Pagan p is 8.6e-48, so HC3 robust standard errors are used.

**Result.**

- r2 business: 0.3543
- skew records lost: 50.57
- ks d lognormal: 0.0914
- ks d normal: 0.4858
- adj r2 business: 0.3514
- test rmse business: 1.657
- test rmse full: 1.564
- per record cost inr: 6456

**What it yields.** Holding sector and size fixed, malware attacks raise expected records lost the most, multiplying them by 5.92, and the Information sector has the largest sector or size effect (13.61 times). CyCRS uses this model to estimate records lost for each attack type and multiplies by the cost per record (₹6,456) to price each attack in rupees.

**Limitations.** Business model explains 35.4% of variation; individual breaches vary widely around the estimate. Cost per record is derived from IBM India averages and applied to every attack type. VCDB over represents large and US organisations.

## 8. Which incidents end in data loss (`breach-classifiers`)

Module: 4: Classification (logistic regression, decision tree, KNN, Naive Bayes, LDA, ROC, confusion matrix). Stage: likelihood. Runs live on the user's business: no.

**Question.** Can the kind of attack, attacker and assets involved tell us whether an incident ends in confirmed data disclosure?

**Why this model.** The target is binary and only 9.4% of training incidents are No, so models are compared on AUC and recall/specificity rather than accuracy, and class weights are used where supported. Each model has a data-based reason: logistic, binary target with 24 binary predictors; class weights offset the 542 No cases in training; decision_tree, finds interactions between attack and asset flags as readable rules; depth 10 and leaf 20 chosen by CV AUC; knn, non-parametric baseline on scaled flags; k = 2 minimised CV balanced error; naive_bayes, all predictors are 0/1 flags, so Bernoulli Naive Bayes is the matching likelihood; lda, linear boundary with shared covariance; a classical comparison for logistic regression.

**Result.**

- best model: decision_tree
- youden j: 0.5549
- best cv auc: 0.8263
- youden threshold: 0.4425
- k knn: 2
- tree depth: 10
- tree min leaf: 20

**What it yields.** Decision tree separates data-loss incidents best (CV AUC 0.83), and the strongest logistic signals are action_physical (odds ratio 5.15), sector_health_care_and_social_assistance (odds ratio 4.97), action_error (odds ratio 4.26). With only 542 No cases to learn from, CyCRS treats most incidents as likely to expose data and uses this model only to explain which attack features matter, not to promise a business it is safe.

**Limitations.** Only 775 incidents are confirmed No, so every No-side metric is uncertain. Potentially and Unknown disclosures were dropped; incidents with no confidentiality section count as No, which assumes VERIS coders recorded every exposure. CV AUC SD for the best model is 0.019, so model ranks may change with a new sample.

## 9. Which attacks a business is most exposed to (`attack-likelihood`)

Module: 4: Logistic regression and ROC. Stage: likelihood. Runs live on the user's business: yes.

**Question.** Given a business's sector, size and the kinds of IT assets it relies on, which attack categories are most likely if it has an incident?

**Why this model.** Each target is a binary flag and the inputs are a handful of 0/1 profile features, so logistic regression gives a calibrated probability per category and an odds ratio per feature that a business owner can read. Its formula is a weighted sum and a sigmoid, so the browser reproduces the exact same number from the saved coefficients with no server. Unweighted fits keep probabilities calibrated to the observed category shares (for example 17% for physical).

**Result.**

- auc hacking: 0.8652
- auc malware: 0.84
- auc social: 0.738
- auc error: 0.741
- auc misuse: 0.6899
- auc physical: 0.8922

**What it yields.** A business's profile predicts some attack types much better than others: physical reaches AUC 0.89 while misuse is only 0.69. CyCRS runs these models on the user's profile to rank attack categories by probability, then sends each category to the impact model to price it.

**Limitations.** Asset flags record what was hit in past incidents and are used as a proxy for what a business runs. Probabilities are conditional on an incident happening; the chance of having an incident at all comes from annual_incident_prob. VCDB over represents large and US organisations.

## 10. How many things really describe an incident (`pca`)

Module: 5: Principal component analysis. Stage: segment. Runs live on the user's business: no.

**Question.** How many independent dimensions are hidden in the dozens of yes/no flags that describe each incident?

**Why this model.** The 37 flags overlap heavily (a ransomware flag implies a malware flag, an error flag often comes with media assets), so PCA can compress them into a few uncorrelated components. Kaiser's rule keeps 12 components and 80% of the variance needs 14, which measures how much redundancy there is.

**Result.**

- features: 37
- kaiser: 12
- n80: 14
- pc1 var: 0.1788
- pc2 var: 0.1075

**What it yields.** The 37 incident flags boil down to about 12 independent patterns by Kaiser's rule (14 to keep 80% of the information), led by +action_hacking / +actor_external. That is 32% as many dimensions as flags, so the flags overlap but each still adds information; CyCRS keeps the separate attack categories rather than replacing them with components.

**Limitations.** PCA on binary flags is descriptive; components are linear summaries, not causal factors. Rare flags get large standardised values and can dominate later components.

## 11. Business personas (`personas-kmeans`)

Module: 5: K-means clustering. Stage: segment. Runs live on the user's business: yes.

**Question.** Which groups of similar businesses appear in the incident data, and what attacks hit each group?

**Why this model.** Personas are built only from what a business can tell CyCRS about itself (sector, size, the IT it relies on), so a new user can be placed in one instantly by finding the nearest centroid in the browser. K-means suits this because assignment is a simple distance to 8 saved centres, and the silhouette peaks at k = 8 (0.29).

**Result.**

- k: 8
- silhouette: 0.2915
- n persona 0: 861
- n persona 1: 1734
- n persona 2: 645
- n persona 3: 2003
- n persona 4: 1798
- n persona 5: 1267

**What it yields.** The data splits into 8 personas, such as Mixed sector, small, server, whose incidents most often involve hacking. CyCRS places each user in the nearest persona from their sector, size and IT, and shows what actually happened to similar businesses.

**Limitations.** Personas describe reported incidents, not all businesses. Asset flags are a proxy for what a business runs.

## 12. Checking the personas another way (`hierarchical`)

Module: 5: Hierarchical clustering. Stage: segment. Runs live on the user's business: no.

**Question.** Does a different clustering method find the same business personas?

**Why this model.** Ward linkage merges the pair of groups that least increases within-group variance, the same quantity K-means minimises, so agreement between the two is a fair test of persona stability. The adjusted Rand index between the two labelings is 0.44, where 1 is identical and 0 is chance.

**Result.**

- ari: 0.4392
- k: 8
- sample: 500

**What it yields.** An independent method only partly recovers the personas (adjusted Rand index 0.44), so their broad shape is real but the exact boundaries depend on the algorithm. CyCRS uses them for instant assignment and presents them as rough groupings.

**Limitations.** Based on a 500-row sample. Many identical 0/1 profiles create tied distances.

## 13. Which cyber crimes move together across India (`factor-analysis`)

Module: 5: Factor analysis. Stage: segment. Runs live on the user's business: no.

**Question.** Across Indian states, which kinds of cyber crime tend to rise and fall together?

**Why this model.** Crime rates per lakh are continuous and correlated across states, which is what factor analysis models, and Bartlett's test (p 1.3e-19) checks that the correlations are not all zero. KMO is 0.73 (middling) with only 36 states and UTs, so the factors are usable but based on few cases.

**Result.**

- kmo: 0.7331
- bartlett p: 0
- factors: 2
- states: 36

**What it yields.** Across 36 states and UTs, 2 factors summarise the eight crime rates; F1 groups cyber_stalking + fraud + cheating + blackmail, and Telangana scores highest on it. CyCRS uses this only as context about Indian crime patterns, not as an input to its recommendations.

**Limitations.** Only 36 cases for 8 variables. NCRB counts reported FIRs, which depend on how readily each state registers cyber crime.

## 14. Expected yearly loss in rupees (`expected-loss`)

Module: 6: Probability and expected value. Stage: decide. Runs live on the user's business: yes.

**Question.** How much is each kind of attack expected to cost this business per year, in rupees?

**Why this model.** Risk is chance times cost, so each category's expected annual loss is pi x p_c x I_c with pi 0.468 (fallback level 1_india_msme) and a cost per record of ₹6,456. The attack models give p_c given an incident and the impact model gives records lost on the log scale, so the product keeps every step traceable to one model card.

**Result.**

- annual incident prob: 0.468
- per record cost inr: 6456
- ref total 0: 1.495e+06
- ref total 1: 3.35e+06
- ref total 2: 1.066e+06
- ref total 3: 3.858e+08
- ref total 4: 1.254e+07

**What it yields.** For a small retail shop, CyCRS estimates about ₹14.95 lakh a year of expected loss, most of it from malware. These are estimates built from public averages, and each one carries the source and fallback level of its inputs.

**Limitations.** Probabilities come from reported incidents, not from Indian small businesses directly. Categories can overlap within one incident, so the total may overstate loss. Impact uses IBM India average cost per record for every category. Uncapped, one incident at a small retail shop would be priced at ₹45.68 crore, 1.8 times IBM's India average, because VCDB record counts and IBM costs come from large organisations; small and medium profiles are therefore capped at ₹18.18 lakh and ₹1.05 crore, figures from a UK survey rather than India.

## 15. What to buy first for your budget (`budget-optimiser`)

Module: 6: Optimisation under a budget. Stage: decide. Runs live on the user's business: yes.

**Question.** Which security controls should this business buy first to cut the most expected loss within its budget?

**Why this model.** Each step picks the affordable control that removes the most expected loss per rupee, free controls first, and recomputes after every pick because controls overlap on the same attacks. Against exhaustive search on the 5 reference profiles the greedy plan is at most 0.00% worse, while every step can be shown to the user and it runs instantly in the browser.

**Result.**

- controls scored: 4
- reference budget inr: 50000
- max gap pct: 0

**What it yields.** For a small retail shop with ₹50,000 a year, the plan is Endpoint protection, MFA, Offline or cloud backups, Email filtering, cutting expected loss to 31.7% of the starting estimate. Only 4 controls have sourced effectiveness and cost, so the others are shown as not yet scored rather than guessed.

**Limitations.** 8 controls cannot be ranked until their effectiveness or cost is sourced. Effectiveness figures come from vendor or non-Indian studies. Independence of controls is an assumption.

## 16. Do the recommendations match real attacks (`coverage-hit-rate`)

Module: 4 and 2: Evaluation and hypothesis testing. Stage: evaluate. Runs live on the user's business: no.

**Question.** For past incidents the models never trained on, would CyCRS's top 3 controls have addressed what actually happened?

**Why this model.** A hit rate on incidents the models never saw tests the whole chain, not just one model, and the binary hit outcome makes a two-proportion z-test the natural comparison with a fixed baseline. Only 4 controls can be ranked, and 100% of test incidents get exactly the baseline set, so the test has little room to show a difference.

**Result.**

- n test: 3105
- hit rate: 0.2087
- baseline hit rate: 0.2087
- z: 0
- p value: 1
- cohens h: 0

**What it yields.** On 3105 unseen incidents, CyCRS's top 3 controls addressed what happened 20.9% of the time, against 20.9% for the fixed baseline (p 1). Most misses are attacks like errors and misuse whose controls cannot be scored yet, which is where sourcing more effectiveness data would help most.

**Limitations.** VCDB incidents are not Indian small businesses. Hit means the control addresses the attack type, not that it would have stopped it. Only 4 controls are rankable.

## 17. Replaying real Indian incidents (`case-replay`)

Module: 6: Decision analysis (evaluation on documented cases). Stage: evaluate. Runs live on the user's business: no.

**Question.** If these Indian organisations had asked CyCRS for a plan at a ₹50,000 budget, would its top 3 controls have addressed what actually happened?

**Why this model.** Only 4 Indian incidents are documented well enough to replay, too few for a hit rate, so each case is judged on its own. A verdict per case shows a reader exactly where the advice matches reality and where the source is too thin to judge.

**Result.**

- cases: 4
- assessable: 3
- covered: 3
- budget inr: 50000

**What it yields.** For 3 of the 3 cases whose sources say how the attack worked, CyCRS's top 3 controls at ₹50,000 address that kind of attack. 1 case does not state the method, so it is shown without a verdict rather than counted as a success.

**Limitations.** Four public cases from large organisations, not small businesses. Addressing an attack type does not prove the control would have stopped that incident.

## 18. How much the answer depends on the inputs (`sensitivity`)

Module: 7: Sensitivity analysis. Stage: evaluate. Runs live on the user's business: no.

**Question.** If the published figures behind CyCRS are off, how much do the rupee amounts and the order of recommended controls change?

**Why this model.** Every rupee figure multiplies a few published inputs, so moving one input at a time and watching the result shows which sources matter most. 0 of 24 scenarios change the order of the plan and 0 change which controls are in it, which separates rupee uncertainty from advice uncertainty.

**Result.**

- scenarios: 24
- order changes: 0
- set changes: 0

**What it yields.** The rupee figures move most with the incident probability and least with the effectiveness, so the rupee level is only as good as those published averages. The set of controls to buy stays the same in every scenario, so the advice holds even when the rupee estimates are off.

**Limitations.** One-at-a-time ranges ignore inputs moving together. Only four controls can be scored, which limits how much the plan can change.
