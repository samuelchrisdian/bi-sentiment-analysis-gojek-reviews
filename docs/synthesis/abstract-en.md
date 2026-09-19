# Abstract (English)

<!-- ===== Abstract EN — SIAP TEMPEL ===== -->

App-store reviews are a large but unstructured source of user feedback, which
makes recurring complaints hard to detect systematically. This study analyses
100,000 Gojek app reviews published on Google Play between 21 May 2024 and
31 December 2025, comparing three families of classical algorithms across four
trained variants — ComplementNB, MultinomialNB, LinearSVC, and Logistic
Regression — over 1–2 gram TF-IDF features, using a binary label scheme derived
from star ratings and a dual evaluation protocol that reports every model on the
full test set and on the subset of reviews containing at least five words. The
production model (Logistic Regression) reaches a macro-F1 of 0.9336 and negative
class recall of 0.9315 on the full test set against a majority baseline of
0.4196, while the macro-F1 spread across all four variants is only 1.88 points,
meaning the simplest model performs on par with the most complex one. The main
methodological finding is the gap between the two evaluation sets — 2.59 points
of macro-F1 and 3.70 points of accuracy: because 39.9% of reviews contain two
words or fewer and are almost all positive, metrics computed on the full test set
overstate model capability, and manual inspection shows that 48.0% of the model's
errors stem from star ratings that contradict the review text. LDA topic
extraction over 26,732 negative reviews yields nine complaint categories, the two
largest of which — driver availability (36.15%) and GoFood orders and
cancellations (34.25%) — together cover 70.4% of the complaint corpus. The study
therefore recommends dual evaluation as standard practice for app-review corpora,
and positions the system as a complaint triage tool rather than a replacement for
human reading.

**Keywords:** sentiment analysis; Indonesian language; app reviews; class
imbalance; TF-IDF; LDA topic modelling.

---

<!-- Catatan: angka ditulis dengan titik desimal dan koma ribuan sesuai konvensi
     bahasa Inggris; nilainya identik dengan abstract-id.md.
     Rujukan angka sama dengan abstract-id.md.                                -->
