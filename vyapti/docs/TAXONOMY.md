# The Hetvābhāsa Taxonomy

> **Camera-ready note (Nov 2026).** This document dates from the August 2026 submission. Where it differs from the camera-ready paper or [CHANGELOG.md](../CHANGELOG.md), those take precedence; in particular the specificity analysis, the textual status of the taxonomy, and the scorer versions behind the corpus-level results were corrected.


Version 2.1.0 — 13 categories. Machine-readable source: [`taxonomy/hetvabhasa_v2.1.json`](../taxonomy/hetvabhasa_v2.1.json).

*Hetvābhāsa* (हेत्वाभास, "a reason that merely appears to be one") is the Nyāya tradition's theory of defective grounds. Where Western fallacy taxonomies are largely lists of named rhetorical patterns accumulated over time, hetvābhāsa is a *structural* classification: it asks in which specific way the relation between reason and conclusion fails. That is what makes it usable as a typed diagnostic rather than a label set.

## Primary sources

| ID | Text | Author | Period | Role |
|---|---|---|---|---|
| TS | *Tarka-Saṃgraha* | Annambhaṭṭa | 17th c. CE | Primary definitional source for all five hetvābhāsa categories and their sub-types |
| NNB | *Navya-Nyāya-Bhāṣāpradīpaḥ* | Anonymous (pedagogical manual) | Late tradition | Navya-Nyāya technical vocabulary, pratibandha doctrine, avacchedaka-avacchedya relations |
| NS | *Nyāya Sūtras of Gautama with Vātsyāyana Bhāṣya* | Gautama (Gotama); commentary by Vātsyāyana | ~2nd c. BCE (sūtras); ~4th c. CE (bhāṣya) | Original five-fold hetvābhāsa classification; foundational definitions |
| TCM | *Tattva-Cintāmaṇi* | Gaṅgeśa Upādhyāya | 13th c. CE | Advanced vyāpti analysis; formal precision on avacchedaka relations |

## Verification status

Each category carries an explicit basis. This is stored in the taxonomy itself, not asserted in prose, so it travels with the artifact.

| Basis | Meaning | Categories |
|---|---|---|
| VERIFIED_ROOT_TEXT | Defined in the root text of the *Tarka-Saṃgraha*; passage quoted verbatim in `source_passage_verbatim` | RF-01, RF-02, RF-03, RF-04, RF-05, RF-06, RF-07a, RF-08, RF-12 |
| DERIVED_FROM_COMMENTARY | Built from commentary on a root-text definition; the separate category is ours | RF-07b |
| INFERRED_CLASSICAL_DOCTRINE | A classical doctrine; promoting it to a *hetvābhāsa* type is ours | RF-09, RF-11 |
| NO_TEXTUAL_SOURCE | Modern addition | RF-10 |

**RF-10 has no direct sūtra source at all.** It is a useful category. It is not Navya-Nyāya. Reproduce this listing with `python scripts/audit_taxonomy.py`.

## The five-fold division

The classical division has five parent types. The 13 categories sit beneath them, plus three that extend past the classical scheme.

**Savyabhicāra** (सव्यभिचार) — *Erratic / Deviating Reason*  
A reason that is not uniformly concomitant with the conclusion — it deviates from the required pervasion in one of three possible ways  
<sub>TS Sect. LII–LIII; NNB p. 80 · children: RF-01, RF-02, RF-12</sub>

**Viruddha** (विरुद्ध) — *Contradictory Reason*  
A reason that is pervaded by the negation of the conclusion — it proves the opposite of what is intended  
<sub>TS Sect. LIV; NNB p. 84 · children: RF-03</sub>

**Satpratipakṣa** (सत्प्रतिपक्ष) — *Counterbalanced Reason*  
A reason that is opposed by an equally strong reason proving the negation of the conclusion, leaving the matter inconclusive  
<sub>TS Sect. LV; NNB p. 85 · children: RF-04</sub>

**Asiddha** (असिद्ध) — *Unestablished / Unproved Reason*  
A reason whose validity is not established — either its locus, its inherence in the subject, or its pervasion with the conclusion is unproved  
<sub>TS Sect. LVI; NNB p. 80 · children: RF-05, RF-06, RF-07a, RF-07b</sub>

**Bādhita** (बाधित) — *Defeated / Contradicted Reason*  
A reason whose conclusion is overridden by a stronger, independent source of knowledge such as perception or established fact  
<sub>TS Sect. LVII; NNB p. 86 · children: RF-08</sub>

**Extended** — RF-09, RF-10, RF-11 reach beyond the classical five-fold division. See `extended_categories_note` in the JSON.

---

## Categories

### RF-01 — Erratic Reason — Too General (Over-wide)

**साधारण सव्यभिचार** · *Sādhāraṇa Savyabhicāra* · parent: Savyabhicāra · **VERIFIED** · TS Sect. LIII

> The reason is true but proves nothing — it applies equally to cases where the conclusion holds and where it doesn't.

**Formal.** Let H = reason-property, C = sādhya (conclusion). RF-01 holds when H is present in at least one instance where C is present (sapakṣa) AND H is present in at least one instance where C is absent (vipakṣa). The reason is underdetermined — it fails to discriminate.

**Operational.** Step 1: Identify the reason (H) and conclusion (C). Step 2: Find cases where C is true — does H appear there? Step 3: Find cases where C is false — does H also appear there? Step 4: If H appears in BOTH positive and negative cases → RF-01.

**Source.** *sādhāraṇo hetuḥ yaḥ pakṣa-sapakṣa-vipakṣeṣu vartate*  
“The over-wide mark is that which is found both on the sapakṣa and the vipakṣa, that is, which co-exists both with the sādhya and its negation.”  
<sub>TS Sect. LIII, Nyāya-Bodhinī commentary. Index entry: Sadharana- 44.</sub>

**Classical example.** The mountain has fire, because it is knowable (prameyatvāt) — Knowability resides in sapakṣa (kitchen with fire) AND vipakṣa (lake without fire). The reason is over-wide.

**Modern example.** This drug should work because it has anti-inflammatory properties. — Anti-inflammatory properties appear in drugs that DO and do NOT work for this condition. The reason fails to discriminate.

**Diagnostic question.** Is the reason factually true but logically insufficient to establish the conclusion?

**Not this if:**

- The reason-property is factually FALSE about the subject → RF-06
- You can name a SPECIFIC qualifier that would fix the reasoning → RF-07a
- The reason proves the OPPOSITE of the conclusion → RF-03
- The reason exists ONLY in the subject and nowhere else → RF-02


### RF-02 — Erratic Reason — Too Particular (Peculiar)

**असाधारण सव्यभिचार** · *Asādhāraṇa Savyabhicāra* · parent: Savyabhicāra · **VERIFIED** · TS Sect. LIII

> The reason is unique to this one case — you can't generalize from a sample of one.

**Formal.** Let H = reason-property, S = subject. RF-02 holds when H is found ONLY in S and not in any sapakṣa or vipakṣa. No pervasion can be established from a singleton.

**Operational.** Step 1: Identify the reason (H). Step 2: Does H appear in ANY other case besides the specific subject? Step 3: If H exists ONLY in this one subject → RF-02.

**Source.** *asādhāraṇo hetuḥ yaḥ pakṣa eva asti, na sapakṣa-vipakṣayoḥ*  
“The peculiar mark is found neither in sapakṣa nor vipakṣa — it is a peculiar characteristic of the pakṣa which exists nowhere else.”  
<sub>TS Sect. LIII, Nyāya-Bodhinī. Index: Asadharana- 44, 299.</sub>

**Classical example.** Sound is eternal, because it has the nature of sound (śabdatva) — Śabdatva exists in no sapakṣa and no vipakṣa. No pervasion can be established.

**Modern example.** Albert Einstein developed relativity because he was born in Ulm. — Born-in-Ulm is unique to Einstein. No pervasion can be established from a singleton.

**Diagnostic question.** Is the reason-property unique to the specific subject, with no other instances to compare?

**Not this if:**

- The reason appears in other cases too → RF-01 or valid reasoning
- The reason is factually false → RF-06
- The conclusion is universal/vacuous → RF-12


### RF-03 — Contradictory Reason

**विरुद्ध** · *Viruddha* · parent: Viruddha · **VERIFIED** · TS Sect. LIV; NNB p. 84

> The reason proves the exact opposite of what the arguer claims.

**Formal.** Let H = reason, C = conclusion. RF-03 holds when H is pervaded by NOT-C rather than C. Whenever H is present, NOT-C follows.

**Operational.** Step 1: Identify the reason (H) and conclusion (C). Step 2: Ask — does H actually support C, or does it support NOT-C? Step 3: If H entails NOT-C → RF-03.

**Source.** *viruddho hetuḥ yo sādhya-viparyayasya vyāpakaḥ*  
“Contrary reason is that which is pervaded by the negation of the sādhya. The fallacy consists in drawing a conclusion just contrary to that which would be justified by the reason.”  
<sub>TS Sect. LIV. Gotama Sūtra I, 2, 47. Index: Viruddha- 44, 45, 206.</sub>

**Classical example.** Sound is eternal, because it is artificial (kṛtakatvāt) — Artificiality is pervaded by non-eternality, the opposite of eternality.

**Modern example.** This policy is safe because it has never been tested. — 'Never tested' entails lack-of-established-safety, the negation of 'safe'.

**Diagnostic question.** Does the SAME reason, properly analyzed, entail the OPPOSITE of the stated conclusion?

**Not this if:**

- The opposition comes from a SEPARATE, DIFFERENT reason → RF-04
- The opposition comes from external evidence, not from the reason itself → RF-08
- The assertion itself is self-undermining → RF-10


### RF-04 — Counterbalanced Reason

**सत्प्रतिपक्ष** · *Satpratipakṣa* · parent: Satpratipakṣa · **VERIFIED** · TS Sect. LV; NNB p. 85

> There's an equally good argument for the opposite conclusion, but the inference only presents one side.

**Formal.** Let H1 = stated reason, C = conclusion, H2 = counter-reason. RF-04 holds when H2 (distinct from H1) establishes NOT-C with equal or greater strength than H1 establishes C, AND the inference fails to acknowledge H2.

**Operational.** Step 1: Identify the stated reason (H1) and conclusion (C). Step 2: Ask — does a SEPARATE, INDEPENDENT reason (H2) exist that supports NOT-C? Step 3: Is H2 of comparable strength to H1? Step 4: If YES to both, and H2 is not acknowledged → RF-04.

**Source.** *satpratipakṣo hetuḥ yatra sādhya-viparyayasya sādhanam api asti*  
“In satpratipakṣa the hetu proving sādhya-negation is different from that actually given. An inference counterbalanced by a contrary inference of equal weight does not remove doubt.”  
<sub>TS Sect. LV. Gotama Sūtra I, 2, 48. Index: Satpratipaksa- 44, 48, 84, 298.</sub>

**Classical example.** Sound is eternal, because it is audible. Counter: Sound is non-eternal, because it is a creation. — Two independent reasons of comparable strength oppose each other. Neither prevails.

**Modern example.** Bitcoin is a good investment because it has delivered 100x returns over 10 years. — Counter: 80%+ drawdowns and no cash flow. Both reasons valid; inference cherry-picks one side.

**Diagnostic question.** Does a SEPARATE, DISTINCT reason of comparable strength exist for the opposite conclusion?

**Not this if:**

- The SAME reason proves the opposite → RF-03 (internal contradiction)
- The opposition comes from established fact, not a competing inference → RF-08
- The opposing evidence is clearly weaker → not RF-04 (the opposition must be comparable strength)
- The argument merely MENTIONS alternatives without presenting them as valid competing reasons → RF-09 (spurious causal claim). RF-04 requires TWO actively presented, genuinely valid, competing reasons of comparable strength.


### RF-05 — Unestablished Reason — Non-Existent Locus (Subject)

**आश्रयासिद्ध** · *Āśrayāsiddha* · parent: Asiddha · **VERIFIED** · TS Sect. LVI

> The thing being argued about doesn't exist in the first place.

**Formal.** Let S = subject (pakṣa). RF-05 holds when S does not exist — the entity is fictitious or fabricated.

**Operational.** Step 1: Identify the subject of the inference. Step 2: Can you verify this entity exists? Step 3: If NO → RF-05.

**Source.** *āśrayāsiddhaḥ pakṣa-dharmasya pakṣa eva asiddheḥ*  
“Non-existent subject: the skyey lotus is fragrant because it is a lotus. Here the subject does not exist at all.”  
<sub>TS Sect. LVI. Index: Asrayasiddha- 46; Asiddha- 44, 46, 305.</sub>

**Classical example.** The sky-lotus is fragrant, because it is a lotus. — The sky-lotus does not exist. No properties can be inferred about it.

**Modern example.** Dr. Sarah Chen's 2019 Stanford study shows intermittent fasting reduces dementia risk by 47%. — Dr. Sarah Chen does not exist. The locus is fabricated.

**Diagnostic question.** Does the subject entity actually exist?

**Not this if:**

- The subject exists but a property attributed to it is false → RF-06
- The subject is real and the error is in the reasoning → other categories


### RF-06 — Unestablished Reason — Non-Existent Property

**स्वरूपासिद्ध** · *Svarūpāsiddha* · parent: Asiddha · **VERIFIED** · TS Sect. LVI

> The thing is real, but what's being said about it is wrong.

**Formal.** Let S = subject, H = reason-property. RF-06 holds when S exists BUT H does not actually inhere in S. The property attributed to the subject is factually false.

**Operational.** Step 1: Confirm the subject exists (if not → RF-05). Step 2: Check — is the reason-property FACTUALLY TRUE of this subject? Step 3: If the property is demonstrably FALSE → RF-06.

**Source.** *svarūpāsiddhaḥ hetoḥ tad-āśraya eva asiddheḥ*  
“Non-existent reason: Sound is a quality because it is ocular. Here Sound is not ocular. The hetu itself is non-existent on the pakṣa.”  
<sub>TS Sect. LVI. Index: Svarupasiddha- 46.</sub>

**Classical example.** Sound is a quality, because it is ocular. — Sound exists but ocularity does not reside in sound — sound is audible, not ocular.

**Modern example.** The Eiffel Tower was built in 1820, therefore it pre-dates the Industrial Revolution. — Eiffel Tower exists. 'Built in 1820' is false (built 1889). Property false → RF-06.

**Diagnostic question.** Is the reason-property factually false when checked against empirical evidence?

**Not this if:**

- The subject ITSELF doesn't exist → RF-05
- The property is TRUE but the reasoning from it is too broad → RF-01
- The property is TRUE but the pervasion is conditional → RF-07a
- The property is TRUE but proves the opposite → RF-03


### RF-07a — Unestablished Pervasion — Missing Universal Qualifier (Upādhi Problem)

**व्याप्यत्वासिद्ध (सोपाधिक)** · *Vyāpyatvāsiddha (Sopādhika)* · parent: Asiddha · **VERIFIED** · TS Sect. LVI; TS Sect. on Upādhi (§ 46–47)

> The rule works, but only under certain conditions that aren't stated.

**Formal.** Let H = reason, C = conclusion, U = upādhi. RF-07a holds when the stated pervasion H → C is actually (H ∧ U) → C. U pervades C but does not pervade H. The pervasion is conditional but presented as unconditional.

**Operational.** Step 1: State the claimed pervasion: 'Whenever H, then C.' Step 2: Find a counterexample — a case where H is true but C is false. Step 3: Identify what's DIFFERENT in that counterexample — what condition is ABSENT? Step 4: That absent condition is the missing upādhi → RF-07a.

**Source.** *vyāpyatvāsiddhe sopādhibhūto hetuḥ*  
“Non-existent concomitance involves a limitation or condition (upādhi). Condition is that which pervades the thing to be proved but does not pervade the reason.”  
<sub>TS Sect. LVI. Index: Vyapyatvasiddha- 46; Upadhi- 46, 47, 310; Sopadhika- 46.</sub>

**Classical example.** The mountain is smoky, because it has fire. — Fire → smoke only when wet fuel contact exists. Wet fuel is the upādhi.

**Modern example.** Antibiotics will cure this infection. — Conditional on bacterial type, resistance, dosing. Upādhis are unstated.

**Diagnostic question.** Can you name a SPECIFIC condition (upādhi) that the pervasion depends on but that is not stated?

**Not this if:**

- You CANNOT name a specific qualifier — the reason just appears in vipakṣa generally → RF-01
- The general rule holds but fails for THIS specific subject → RF-07b
- The reason-property itself is factually false → RF-06


### RF-07b — Unestablished Pervasion — Missing Contextual Qualifier for This Subject

**व्याप्यत्वासिद्ध (विशेष)** · *Vyāpyatvāsiddha (Viśeṣa)* · parent: Asiddha · **INFERRED** · TS Sect. LVI (commentary); NNB pp. 60–72

> The general rule works, but not for this particular case.

**Formal.** Let H = reason, C = conclusion, S = specific subject, U_s = subject-specific qualifier. RF-07b holds when H → C is generally established BUT a condition of this particular S defeats the pervasion for S.

**Operational.** Step 1: Confirm the general rule H → C is valid. Step 2: Check — does this SPECIFIC subject have a condition that defeats the general rule? Step 3: If YES → RF-07b.

**Classical example.** This son of Mitrā is dark-coloured, because he is a son of Mitrā. — General association holds for elder brothers (who had vegetable diet). This son born after ghee diet — contextual condition absent.

**Modern example.** This patient should take ibuprofen because ibuprofen reduces fever. — General rule valid. This patient has kidney disease. Contextual qualifier absent.

**Diagnostic question.** Does the general rule hold, but fail for THIS specific subject due to a subject-specific condition?

**Not this if:**

- The general rule ITSELF is conditional → RF-07a
- The reason-property is factually false → RF-06
- A blocker prevents the causal chain → RF-11 (overlaps; see note)


### RF-08 — Defeated Reason — Contradicted by Stronger Evidence

**बाधित** · *Bādhita* · parent: Bādhita · **VERIFIED** · TS Sect. LVII; NNB p. 86

> The conclusion is simply wrong — known facts disprove it, regardless of how the argument is structured.

**Formal.** Let H = reason, C = conclusion, K = independent knowledge source. RF-08 holds when K directly establishes NOT-C, defeating the conclusion.

**Operational.** Step 1: Identify the conclusion. Step 2: Is there independently established, verifiable evidence that directly contradicts it? Step 3: If YES → RF-08.

**Source.** *bādhito hetuḥ yatra sādhyam anya-pramāṇena nivāryate*  
“A reason is bādhita where the negation of the sādhya is established by another and more authoritative proof.”  
<sub>TS Sect. LVII. Index: Badhita- 44, 48, 315.</sub>

**Classical example.** Fire is cold, because it is a substance. — Defeated by tactile perception — we perceive fire as hot.

**Modern example.** The Earth must be the center of the solar system because the Sun appears to move. — Defeated by heliocentric evidence.

**Diagnostic question.** Is the conclusion directly contradicted by independently established facts, perception, or stronger evidence?

**Not this if:**

- The opposition comes from WITHIN the reason itself → RF-03
- The opposition is from an equally strong competing inference → RF-04
- The reason-property is factually false (the problem is in the premise, not the conclusion) → RF-06


### RF-09 — Explained by Another Cause — Causally Redundant Reason

**अन्यथासिद्ध** · *Anyathāsiddha* · parent: Extended · **INFERRED** · TS Sect. XXVI; NNB pp. 87–93

> Post hoc fallacy — claiming X caused Y when Y was already explained by something else.

**Formal.** Let H = proposed cause, C = effect, K = independent cause. RF-09 holds when K fully accounts for C, making H causally redundant.

**Operational.** Step 1: Identify the claimed cause (H) and effect (C). Step 2: Is there an alternative cause (K) that fully explains C? Step 3: Is K sufficient WITHOUT H? Step 4: If YES → RF-09.

**Source.** *anyathāsiddho hetuḥ yasya kāryatva-ādi-sambandho anyena eva siddhaḥ*  
“That which is otherwise established — the causal relation is already accounted for by another independent cause.”  
<sub>TS Sect. XXVI and NNB. Index: Anyathasiddha- 26, 192.</sub>

**Classical example.** The potter's ass is the cause of the pot. — The clay can be transported by other means. The ass is redundant.

**Modern example.** The patient recovered because we administered homeopathic remedy X. — Recovery explained by natural immune response. Remedy is redundant.

**Diagnostic question.** Is the proposed cause actually necessary, or is the effect already explained by an independent cause?

**Not this if:**

- The reason is too broad (logical error) → RF-01
- The conclusion is defeated by external facts → RF-08
- A blocker prevents the causal chain → RF-11


### RF-10 — Performative Self-Refutation

**प्रागुक्त-विरुद्ध-बाधित-संयोग** · *Prāgukta-Viruddha-Bādhita-Saṃyoga* · parent: Extended · **INFERRED** · NO DIRECT SŪTRA SOURCE

> The claim destroys itself just by being said.

**Formal.** Let A = act of assertion, C = content of claim. RF-10 holds when A constitutes evidence that defeats C.

**Operational.** Step 1: State the claim. Step 2: Ask — does the ACT of making this claim undermine the claim's truth-conditions? Step 3: If YES → RF-10.

**Classical example.** N/A — no traditional Nyāya example. INFERRED category. — Closest analogue: viruddha where the hetu is the act of speaking itself.

**Modern example.** I am completely certain that no claims can be made with certainty. — Asserting certainty defeats claim of no certainty.

**Diagnostic question.** Does the act of asserting this claim undermine the claim itself?

**Not this if:**

- The contradiction is between the reason and conclusion (not the assertion act) → RF-03
- The defeat comes from external facts → RF-08


### RF-11 — Blocked Causal Chain

**प्रतिबन्ध** · *Pratibandha* · parent: Extended · **INFERRED** · NNB pp. 72–80

> Everything is in place for the expected result, but something is blocking it.

**Formal.** Let H = causal conditions, C = effect, B = blocker (pratibandha). RF-11 holds when all conditions for C are present BUT B prevents C from occurring.

**Operational.** Step 1: Confirm all standard causal conditions are present. Step 2: Is there a blocking condition that prevents the expected outcome? Step 3: If YES → RF-11.

**Source.** *pratibandhakatvam — pratibadhyati bādhate yaḥ sa pratibandhakaḥ, tasya bhāvaḥ pratibandhakatvam*  
“Blockerhood: that which blocks is a pratibandha; its absence is the condition required for the causal chain to complete.”  
<sub>NNB pp. 72–80. Jewel-fire example. VERIFIED for concept; INFERRED for hetvābhāsa classification.</sub>

**Classical example.** Fire will burn this object — fire and combustible material are present. — A specific jewel (maṇi) blocks the burning. Causal chain blocked.

**Modern example.** This medication will eliminate the tumor. — MDR1 overexpression blocks drug absorption.

**Diagnostic question.** Are all causal conditions present, but a blocker prevents the expected outcome?

**Not this if:**

- The pervasion itself is conditional (missing qualifier) → RF-07a
- The pervasion fails for this subject's context → RF-07b
- The conclusion is simply contradicted by facts → RF-08


### RF-12 — Erratic Reason — Non-Exclusive (Universal Predicate)

**अनुपसंहारी सव्यभिचार** · *Anupasamhārī Savyabhicāra* · parent: Savyabhicāra · **VERIFIED** · TS Sect. LIII

> The conclusion is a tautology or truism that applies to literally everything in existence — it's unfalsifiable because nothing is excluded.

**Formal.** Let C = conclusion. RF-12 holds when C applies to ALL entities in the universe without exception — no vipakṣa can exist because the sādhya is ontologically universal (viśvavyāpi). The pervasion is untestable because there is no negative class.

**Operational.** Step 1: Examine the conclusion (sādhya). Step 2: Does the conclusion apply to ALL entities whatsoever — not just a large class, but literally everything? Step 3: If the conclusion applies to EVERYTHING with zero exceptions in any domain → RF-12. Step 4: If the conclusion applies to a LARGE CLASS but not everything (e.g., 'all politicians', 'all drugs'), counter-instances exist outside that class → NOT RF-12, likely RF-01.

**Source.** *anupasamhārī hetuḥ yatra sādhyam eva viśvavyāpi*  
“The non-exclusive: the sādhya being universal, nothing is excluded from it.”  
<sub>TS Sect. LIII. Index: Anupasarhhāri- 44, 302.</sub>

**Classical example.** All things are nameable, because they are knowable. — Everything is nameable. No vipakṣa. Vacuous.

**Modern example.** AI systems have properties, because they are computational entities. — 'Has properties' is universally true. No counter-instance. Vacuous.

**Diagnostic question.** Does the conclusion apply to ALL entities in the universe without exception — not just to a broad class, but to literally everything?

**Not this if:**

- The conclusion applies to a LARGE CLASS but not to everything (e.g., 'all politicians are corrupt' — non-politicians are counter-instances) → RF-01
- The REASON is too broad (but the conclusion is specific) → RF-01
- The REASON is too narrow → RF-02


---

## Notes on use

**RF-12 is specified but not in the classifier's output space.** It is textually attested and belongs in the taxonomy; it was not part of the calibrated label set the paper reports on. The distinction between a specification and an implementation is deliberate and the paper makes it.

**Vyāpti-8.** Five of twelve categories are effectively inert on found text (see [LIMITATIONS.md](LIMITATIONS.md) §7). The production profile `vyapti.VYAPTI_8` contains only the categories that fire on real text: RF-01, RF-02, RF-03, RF-06, RF-07a, RF-08, RF-09, NONE. The research taxonomy stays complete.

**NONE is a verdict, not a fallback.** A sound argument gets NONE with the same confidence any other label would carry. Everything about the specificity defect follows from the classifier having been calibrated as though this were not true.
