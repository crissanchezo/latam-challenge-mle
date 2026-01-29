# Challenge

## Part I (Model)

According to the results:

| Model | Accuracy | Recall (delay) | F1 (delay) |
| -- | -- | -- | -- |
| XGB without balance | 0.81 | 0.00 | 0.00 |
| LogReg without balance | 0.81 | 0.03 | 0.06 |
| XGB + top 10 features + balance | 0.55 | 0.69 | 0.37 |
| XGB + top 10 features - balance | 0.81 |  0.01 | 0.01 |
| LogReg + top 10 features + balance | 0.55 | 0.69 |   0.36 |
|  LogReg + top 10 features - balance | 0.81 | 0.01 | 0.03 |

The models with 81% of accuracy and zero recall are useless for detect delay. If there are 100 delayed flights and my recall is zero, my model detect none of them.
Since I think delay detection is more important for LATAM's operations I will focus on higher recalls.

| Model | Accuracy | Recall (delay) | F1 (delay) |
| -- | -- | -- | -- |
| XGB + top 10 features + balance | 0.55 | 0.69 | 0.37 |
| LogReg + top 10 features + balance | 0.55 | 0.69 |   0.36 |

Both models have similar performance (0.69), so with that in mind:

* LogisticRegression is simpler and more interpretable.
* There is no evidence that the additional complexity of XGBoost adds value.
So using Occam's razor (aka principle of parsimony), I chose **LogisticRegression with top 10 features and class balancing**.

### Tests

When I ran make model-test from project root

```bash
.                          ← make model-test
├── data/
│   └── data.csv
├── tests/
│   └── model/
│       └── test_model.py 
```

The `../data/data.csv` is relative to the test_model.py. When I run the test in project root `../data/data.csv` is outside the project.
So in the I use this approach:

```text
current_dir: /<path>/challenge_mle/tests/model
data_path: /<path>/challenge_mle/tests/model/../../data/data.csv
```

## Part II (API)

### Dependency Updates

Original dependencies were incompatible with Python 3.12.

| Package | Original | Updated | Reason |
| --------- | ---------- | --------- | -------- |
| FastAPI | ~0.86.0 | >=0.110.0 | Python 3.12 + Pydantic v2 support |
| Pydantic | ~1.10.2 | >=2.0.0 | Modern validation syntax |
| uvicorn | ~0.15.0 | >=0.23.0 | Python 3.12 compatibility |
| pandas | ~1.3.5 | >=2.0.0 | Python 3.12 compatibility |
| numpy | ~1.22.4 | >=1.26.0 | Python 3.12 compatibility |

### Design Decisions

1. Application startup
    The model is loaded and trained at startup for simplicity given the challenge scope.
    Loading a pre-trained model (pickle) at startup instead of training on-the-fly would be more production-appropriate.

    > **Fail-fast approach**: No try/catch around startup logic. If CSV loading or model training fails, the application does not start. This prevents running in an inconsistent state.

2. Input Validation with Pydantic
    Created `Flight` and `PredictRequest` models with field validators:

    * **MES**: Must be between 1 and 12
    * **TIPOVUELO**: Must be "I" (International) or "N" (National)
    * **OPERA**: Validated at runtime against operators loaded from CSV

3. HTTP 400 vs 422
    FastAPI/Pydantic returns HTTP 422 for validation errors by default. I change that in an custom exception handler to return HTTP 400 as required by tests.

## Part III (deploy)

For this part I used GCP and Terraform. With this I provisioned the following GCP resources:

* **Artifact Registry**: Docker image repository
* **Cloud Run**: Serverless container hosting
* **IAM Policy**: Public access (unauthenticated)

### Cloud Run Configuration

| Setting | Value | Reason |
| --------- | ------- | -------- |
| CPU | 1 | Sufficient for ML inference |
| Memory | 1Gi | Model + pandas operations |
| Min instances | 0 | Scale to zero (cost optimization) |
| Max instances | 3 | Limit costs during stress test |
| Ingress | All traffic | Public API access |

### Build & Deploy

1. Enable the Artifact Registry and Cloud Run APIs in GCP.
2. Create an Artifact Registry repository.
3. Build the image locally (pay special attention to the local architecture).
4. Push the image.
5. Deploy the API.
6. Configure IAM to grant unauthenticated access to the API.

```bash
cd terraform
terraform init

terraform apply -target=google_artifact_registry_repository.repo

gcloud auth configure-docker us-central1-docker.pkg.dev

# I specified the platform since my machine have macOS
docker build --platform linux/amd64 -t us-central1-docker.pkg.dev/TU_PROYECTO/latam-challenge/latam_api:latest .
docker push us-central1-docker.pkg.dev/TU_PROYECTO/latam-challenge/latam_api:latest

terraform apply

terraform output cloud_run_url
```

### Stress Test Results

| Metric | Value |
| -------- | ------- |
| Total requests | 7,264 |
| Failures | 0 (0.00%) |
| Avg response time | 220ms |
| Median response time | 210ms |
| Throughput | 126 req/s |
| P95 | 290ms |
| P99 | 430ms |

### Cleanup

```bash
terraform destroy
```

## Part IV (CI/CD)

Enable IAM Service Account Credentials.

## Local execution

```bash
uv venv
source .venv/bin/activate

uv pip install -e .[dev,test]

pytest
jupyter notebook
```

## Notes

* This project requires Python ≥ 3.12.
* Some dependencies were updated to ensure compatibility.
* Since the code was ran on a Mac, OpenMP had to be installed for dependency xgboost.
