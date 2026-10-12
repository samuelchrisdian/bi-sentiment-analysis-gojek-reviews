# Abstract (English)

<!-- ===== Abstract EN — SIAP TEMPEL ===== -->

App-store reviews are a large but unstructured source of user feedback, which
makes recurring complaints and release-to-release shifts in sentiment hard to
monitor systematically. This study collected its own corpus of Gojek app reviews
from Google Play Indonesia over five years (October 2021 – September 2026) and
analyses 526,322 reviews; the 14,671 reviews (2.8%) written predominantly in
English were translated into Indonesian with the MarianMT machine translation
model. Binary sentiment classification is built on 1–2 gram TF-IDF features
with labels derived from star ratings; the production model was selected from four
variants of three classical algorithm families through a decision framework
fixed in advance, and evaluated with a dual protocol on the full test set and on
reviews containing at least five words. The selected model, Logistic Regression,
reaches a macro-F1 of 0.9261 and negative class recall of 0.9192 on the full
test set against a majority baseline of 0.4154, yet its macro-F1 drops by 3.10
points to 0.8951 on informative reviews: 40.6% of reviews contain two words or
fewer and are almost all positive, while manual inspection of 50
misclassifications shows that 50.0% of them stem from star ratings that
contradict the review text. LDA topic modelling over negative reviews, followed
by keyword-based category assignment, yields five complaint categories, led by
driver search and assignment, waiting time and order cancellation (38.20% of
negative reviews) and customer service (28.20%), with moderate agreement with an
independent rater (κ = 0.5430). Descriptively, the share of reviews predicted
negative ranges from 20.67% to 56.62% per month and from 17.66% to 60.63% across
198 app versions, with the highest monthly value occurring in the final month of
the data. The study concludes that dual evaluation should be standard practice
for app-review corpora, and that the system is best positioned as a tool for
complaint triage and for monitoring complaints over time and across releases,
rather than as a replacement for human reading.

**Keywords:** sentiment analysis; Indonesian language; app reviews; machine
translation; class imbalance; TF-IDF; LDA topic modelling.

---

<!-- Catatan: angka ditulis dengan titik desimal dan koma ribuan sesuai konvensi
     bahasa Inggris; nilainya identik dengan abstract-id.md.
     Rujukan angka sama dengan abstract-id.md.                                -->
