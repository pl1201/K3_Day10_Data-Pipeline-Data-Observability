# Phan cong Day 10 - Nhom 5 thanh vien

## 1. Pham vi phu trach

| Thanh vien | Vai tro | File chinh |
|---|---|---|
| Thanh vien 1 | Source Ingestion | `src/ingestion/crossref.py` |
| Thanh vien 2 | Cleaning & Test set | `src/ingestion/cleaning.py`, `src/evaluation/testset.py` |
| Thanh vien 3 | Observability | `src/observability/quality.py`, `src/observability/reporting.py` |
| Thanh vien 4 | Corruption & Repair | `src/ingestion/corruption.py` |
| Thanh vien 5 | Integration & Comparison | `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py` |

## 2. Quy tac lam viec chung

- Khong chay corruption khi baseline chua tao du artifact.
- Baseline, corrupted va repaired phai dung path/collection rieng.
- Giu nguyen test set, ground truth, evaluator va top-k khi so sanh ba trang thai.
- Repair phai chay lai tu raw/source dang tin cay, khong sua tay answers hoac metrics.
- Moi lan ban giao can co artifact, record count va loi/blocker kem bang chung.
- Report phai doc so lieu tu artifact that; khong hard-code ket qua.
- Khong commit API key, `.env` hoac credential.

## CP0 - Khoi dong, contract va ingestion raw (00:00-00:30)

### Thanh vien 1 - Source Ingestion

1. Doc contract `PaperRecord` va Crossref payload; chot cach tao DOI/`paper_id` on dinh.
2. Liet ke raw response, raw records va metadata nguon can luu.
3. Ban giao sample raw va schema field cho Thanh vien 2, Thanh vien 5.

### Thanh vien 2 - Cleaning & Test set

1. Chot clean schema va quy tac xu ly null, date, duplicate, `text_for_embedding`.
2. Thiet ke test set gom `id`, `type`, `question`, `ground_truth`, `ground_truth_doc_ids`.
3. Ban giao clean schema va test-set format cho Thanh vien 3, Thanh vien 5.

### Thanh vien 3 - Observability

1. Chot cac signal: row count, missing, duplicate, freshness va `age_days`.
2. Phac cau truc report va lien ket tu chi so toi artifact nguon.
3. Ban giao quality/report checklist cho Thanh vien 5.

### Thanh vien 4 - Corruption & Repair

1. Chon corruption do duoc: missing, drop, noise, old date va duplicate.
2. Dinh nghia corruption log: loai loi, record ID, tham so va before/after.
3. Ban giao corruption contract va dieu kien repair cho Thanh vien 5.

### Thanh vien 5 - Integration & Comparison

1. Lap flow `raw -> clean -> test set/index -> evaluate -> quality -> report`.
2. Chot paths cho baseline, corrupted va repaired.
3. Xac nhan dependency, artifact va tieu chi hoan thanh cua ca nhom.

**Checkpoint dat khi:** contract thong nhat, raw sample ton tai va moi thanh vien biet dau vao/dau ra cua minh.

## CP1 - Cleaning, data model va quality gates (00:30-01:05)

### Thanh vien 1

1. Hoan thien `parse_crossref_payload` va stable `paper_id`.
2. Fetch voi timeout/retry cho 429/503; luu raw response truoc khi parse.
3. Ban giao raw paths, record count va sample hop le cho Thanh vien 2.

### Thanh vien 2

1. Normalize title, summary, authors, categories va published date.
2. Dedupe, tinh `age_days`, tao `text_for_embedding` va ghi ly do record bi loai.
3. Ban giao clean CSV/JSON cung raw/clean counts cho Thanh vien 3, Thanh vien 5.

### Thanh vien 3

1. Hoan thien checks row count, unique `paper_id`, missing va duplicate.
2. Tinh freshness tu published date/`age_days`.
3. Ban giao quality JSON/report so bo va danh sach loi cho Thanh vien 2.

### Thanh vien 4

1. Viet test case cho tung phep corruption tren dataframe mau.
2. Xac minh corruption khong mutate dataframe dau vao.
3. Xac minh log co du before/after va ban giao danh sach scenario da test.

### Thanh vien 5

1. Ra soat contract raw-clean va khoa ten/path artifact.
2. Chay import, schema check va mot sample xuyen suot pipeline.
3. Chi mo buoc index/test set khi clean gate dat; ghi blocker kem evidence.

**Checkpoint dat khi:** clean artifact doc duoc, `paper_id` unique, cac field bat buoc ton tai va record bi loai truy vet duoc.

## CP2 - Test set, RAG index va smoke test (01:05-01:35)

### Thanh vien 1

1. Theo doi mot `paper_id` tu raw toi clean.
2. Xu ly field nguon con thieu va co dinh raw snapshot.
3. Cung cap source evidence khi ground truth can doi chieu.

### Thanh vien 2

1. Hoan thien `build_test_set` tu cleaned data.
2. Dam bao cau hoi kiem chung duoc va moi `ground_truth_doc_ids` deu ton tai.
3. Ban giao `test_set.json` va thong ke loai cau hoi cho Thanh vien 5.

### Thanh vien 3

1. Audit clean artifact truoc khi index: count, uniqueness, missing va freshness.
2. Chuan bi reporting template nhan dung paths va metrics JSON.
3. Ban giao quality gate PASS/FAIL cho Thanh vien 5.

### Thanh vien 4

1. Chon record corruption dua tren test set de impact co the do duoc.
2. Ghi expected signal/metric change cho tung scenario.
3. Ban giao corruption plan, chua sua bat ky baseline artifact nao.

### Thanh vien 5

1. Tao baseline embeddings/collection va luu embedding manifest.
2. Chay semantic search, exact lookup va agent voi cau hoi trong test set.
3. Ban giao baseline collection va smoke-test evidence.

**Checkpoint dat khi:** `test_set.json`, manifest va baseline collection ton tai; search/lookup/agent tra ket qua co nguon.

## CP3 - Baseline end-to-end va bao cao (01:35-02:00)

### Thanh vien 1

1. Xac minh raw artifacts doc duoc va raw-clean lineage khong dut.
2. Doi chieu raw/clean count va giai thich chenh lech bang log.
3. Ban giao xac nhan source snapshot cho baseline report.

### Thanh vien 2

1. Xac minh clean schema, test set va document IDs truoc evaluation.
2. Sua data/test case sai contract; khong va metrics.
3. Ban giao clean/test-set gate PASS cho Thanh vien 5.

### Thanh vien 3

1. Chay quality va freshness tren baseline.
2. Tao `phase1_report.md` tu artifact that.
3. Doi chieu moi so trong report voi JSON/CSV nguon.

### Thanh vien 4

1. Review kha nang khoi phuc tung corruption tu raw snapshot.
2. Khoa scenario, seed/tham so va output paths cho CP5.
3. Ban giao corruption runbook cho Thanh vien 5.

### Thanh vien 5

1. Hoan thien `phase1.py` va chay baseline end-to-end.
2. Tao answers, `baseline_metrics.json`, collection/manifest va goi reporting.
3. Giai thich it nhat mot retrieval hit/miss bang artifact that.

**Checkpoint dat khi:** metrics, answers, quality/freshness va phase-1 report ton tai, khop nhau.

## CP4 - Nghi va khoa baseline (02:00-02:15)

- Thanh vien 1: khoa raw snapshot se dung de repair.
- Thanh vien 2: khoa clean/test-set count hoac checksum.
- Thanh vien 3: ghi lai baseline signals/metrics lam moc.
- Thanh vien 4: khoa corruption scenario va tham so.
- Thanh vien 5: kiem tra baseline checklist va ghi blocker con lai.

## CP5 - Corruption co kiem soat va do impact (02:15-03:15)

### Thanh vien 1

1. Xac nhan raw source nguyen ven va khong fetch snapshot moi.
2. Cung cap lineage cho record bi drop/corrupt.
3. Ban giao raw recovery path cho Thanh vien 4, Thanh vien 5.

### Thanh vien 2

1. Xac nhan corrupted data van dung schema toi thieu de evaluate.
2. Giu nguyen test set va ground truth.
3. Ban giao corrupted schema gate cho Thanh vien 3, Thanh vien 5.

### Thanh vien 3

1. Chay quality/freshness tren corrupted artifact va luu rieng.
2. Tao corruption report tu log, quality va metrics that.
3. Ghi ro signal thay doi va khong thay doi, khong ket luan qua evidence.

### Thanh vien 4

1. Hoan thien `corrupt_clean_dataframe` theo scenario da khoa.
2. Ghi record ID, type, parameter va before/after vao corruption log.
3. Ban giao corrupted clean va corruption log; baseline khong bi mutate.

### Thanh vien 5

1. Hoan thien flow `corrupt -> rebuild -> evaluate -> observe`.
2. Dung collection/path rieng va test set baseline da khoa.
3. Ban giao corrupted answers/metrics va bang chung baseline khong bi ghi de.

**Checkpoint dat khi:** corrupted clean/index/answers/metrics/quality/report va corruption log deu ton tai.

## CP6 - Repair, comparison, review va demo (03:15-04:00)

### Thanh vien 1

1. Nap lai dung raw snapshot baseline.
2. Chung minh lineage cua cac record da duoc phuc hoi.
3. Kiem tra API key va `.env` khong nam trong artifact/Git.

### Thanh vien 2

1. Chay lai cleaning tu raw de tao repaired data.
2. Khong copy baseline hoac sua tay corrupted data.
3. Ban giao repaired clean cung schema/count/test-ID gate.

### Thanh vien 3

1. Chay repaired quality/freshness.
2. Tao comparison report cho baseline-corrupted-repaired va delta.
3. Doi chieu report voi JSON; ghi ro phan chua phuc hoi.

### Thanh vien 4

1. Doi chieu corruption log voi repaired records.
2. Xac nhan tung corruption da duoc loai bo hoac ghi ro loi con lai.
3. Ban giao evidence before/corrupted/repaired cho demo.

### Thanh vien 5

1. Hoan thien repair va comparison trong `corruption_flow.py`.
2. Evaluate repaired bang cung test set, evaluator va top-k; tinh delta ba trang thai.
3. Chay checklist cuoi va dieu phoi demo theo artifact that.

**Checkpoint dat khi:** repaired artifacts va comparison report day du; ket qua demo tai lap duoc va khong co secret.

## 3. Ma tran ban giao

| Nguoi giao | Artifact chinh | Nguoi nhan |
|---|---|---|
| Thanh vien 1 | Raw response, raw records, lineage/source evidence | Thanh vien 2, 4, 5 |
| Thanh vien 2 | Clean data, test set, schema/count gates | Thanh vien 3, 5 |
| Thanh vien 3 | Quality/freshness outputs, phase-1 va comparison reports | Thanh vien 5 |
| Thanh vien 4 | Corrupted data, corruption log, repair evidence | Thanh vien 3, 5 |
| Thanh vien 5 | Baseline/corruption/repaired runs, answers, metrics, comparison | Ca nhom |

## 4. Checklist truoc khi nop

- [ ] Raw, clean, test set, answers, metrics, quality va reports deu ton tai.
- [ ] Baseline, corrupted va repaired khong ghi de lan nhau.
- [ ] Cung test set, evaluator va top-k duoc dung cho ca ba trang thai.
- [ ] Corruption log khop voi corrupted data.
- [ ] Repaired data duoc tao lai tu raw snapshot.
- [ ] So lieu trong report khop voi artifact JSON/CSV.
- [ ] It nhat mot hit/miss va mot corruption impact duoc giai thich bang evidence.
- [ ] Khong co secret, API key hoac `.env` trong Git.
