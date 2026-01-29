# Challenge

## Part I (Model)

According to the results:

| Model                                  | Accuracy | Recall (delay) | F1 (delay) |
| -------------------------------------- | -------- | -------------- | ---------- |
| XGB without balance                    | 0.81     | 0.00           | 0.00       |
| LogReg without balance                 | 0.81     | 0.03           | 0.06       |
| XGB + top 10 features + balance        | 0.55     | 0.69           | 0.37       |
| XGB + top 10 features - balance        | 0.81     | 0.01           | 0.01       |
| LogReg + top 10 features + balance     | 0.55     | 0.69           | 0.36       |
| LogReg + top 10 features - balance     | 0.81     | 0.01           | 0.03       |

The models with 81% accuracy and near-zero recall are useless for detecting delays. If there are 100 delayed flights and my recall is zero, my model detects none of them.

Since I think delay detection is more important for LATAM's operations, I will focus on higher recall.

| Model                              | Accuracy | Recall (delay) | F1 (delay) |
|------------------------------------|----------|----------------|------------|
| XGB + top 10 features + balance    | 0.55     | 0.69           | 0.37       |
| LogReg + top 10 features + balance | 0.55     | 0.69           | 0.36       |

Both models have similar performance (~0.69 recall), so with that in mind:

- LogisticRegression is simpler and more interpretable.
- There is no evidence that the additional complexity of XGBoost adds value.

Using Occam's razor (aka principle of parsimony), I chose **LogisticRegression with top 10 features and class balancing**.

### Tests

When running `make model-test` from project root:

```text
.                          <- make model-test runs here
├── data/
│   └── data.csv
├── tests/
│   └── model/
│       └── test_model.py 
```

The path `../data/data.csv` is relative to `test_model.py`. When running from project root, `../data/data.csv` points outside the project.

Solution: Use absolute path based on `__file__`:

```python
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "../../data/data.csv")
```

## Part II (API)

### Dependency Updates

Original dependencies were incompatible with Python 3.12.

| Package   | Original | Updated   | Reason                            |
| --------- | -------- | --------- | --------------------------------- |
| FastAPI   | ~0.86.0  | >=0.110.0 | Python 3.12 + Pydantic v2 support |
| Pydantic  | ~1.10.2  | >=2.0.0   | Modern validation syntax          |
| uvicorn   | ~0.15.0  | >=0.23.0  | Python 3.12 compatibility         |
| pandas    | ~1.3.5   | >=2.0.0.  | Python 3.12 compatibility         |
| numpy     | ~1.22.4  | >=1.26.0  | Python 3.12 compatibility         |

### Design Decisions

#### 1. Application Startup

The model is loaded and trained at startup for simplicity given the challenge scope. Loading a pre-trained model (pickle) at startup instead of training on-the-fly would be more production-appropriate.

> **Fail-fast approach**: No try/catch around startup logic. If CSV loading or model training fails, the application does not start. This prevents running in an inconsistent state.

#### 2. Input Validation with Pydantic

Created `Flight` and `PredictRequest` models with field validators:

- **MES**: Must be between 1 and 12
- **TIPOVUELO**: Must be "I" (International) or "N" (National)
- **OPERA**: Validated at runtime against operators loaded from CSV

#### 3. HTTP 400 vs 422

FastAPI/Pydantic returns HTTP 422 for validation errors by default. Added a custom exception handler to return HTTP 400 as required by tests.

## Part III (Deploy)

Used **GCP** and **Terraform** to provision the following resources:

- **Artifact Registry**: Docker image repository
- **Cloud Run**: Serverless container hosting
- **IAM Policy**: Public access (unauthenticated)

### Cloud Run Configuration

| Setting       | Value       | Reason                            |
| ------------- | ----------- | --------------------------------- |
| CPU.          | 1           | Sufficient for ML inference       |
| Memory        | 1Gi         | Model + pandas operations         |
| Min instances | 0           | Scale to zero (cost optimization) |
| Max instances | 3           | Limit costs during stress test    |
| Ingress       | All traffic | Public API access                 |

### Build & Deploy

1. Enable the Artifact Registry and Cloud Run APIs in GCP
2. Create an Artifact Registry repository
3. Build the image locally (pay special attention to the local architecture)
4. Push the image
5. Deploy the API
6. Configure IAM to grant unauthenticated access to the API

```bash
cd terraform
terraform init

terraform apply -target=google_artifact_registry_repository.repo

gcloud auth configure-docker us-central1-docker.pkg.dev

# Platform specified since local machine is macOS (ARM)
docker build --platform linux/amd64 -t us-central1-docker.pkg.dev/PROJECT_ID/latam-challenge/latam-flight-delay-api:latest .
docker push us-central1-docker.pkg.dev/PROJECT_ID/latam-challenge/latam-flight-delay-api:latest

terraform apply

terraform output cloud_run_url
```

### Cleanup

```bash
terraform destroy
```

## Part IV (CI/CD)

### Continuous Integration (`ci.yml`)

**Trigger**: Push to any branch

**Steps**:

1. Checkout code
2. Setup Python 3.12
3. Install dependencies
4. Run model tests (`make model-test`)
5. Run API tests (`make api-test`)

### Continuous Delivery (`cd.yml`)

**Trigger**: Push to `main` branch

**Steps**:

1. Checkout code
2. Authenticate to GCP using Workload Identity Federation
3. Login to Artifact Registry
4. Build Docker image (with caching)
5. Push image with tags: `latest` and `${{ github.sha }}`
6. Deploy to Cloud Run

### GCP Authentication

Used **Workload Identity Federation** instead of service account keys:

- More secure (no long-lived credentials)
- Recommended by Google for GitHub Actions
- Configured via GitHub environment secrets

### Docker Image Strategy

| Tag | Purpose |
| --------- | --------- |
| `latest` | Always points to most recent build |
| `${{ github.sha }}` | Immutable, traceable to specific commit |

### Infrastructure Management

| Component | Managed by |
| --------- | --------- |
| Artifact Registry | Terraform (persistent) |
| Cloud Run Service | Terraform (initial) + CD (updates) |
| IAM Policies | Terraform |

### Secrets Configuration

Stored in GitHub environment `latam_env`:

- `PROJECT_ID`
- `REGION`
- `SERVICE_ACCOUNT`
- `WORKLOAD_IDENTITY_PROVIDER`

> Note: IAM Service Account Credentials API needs to be enabled.

## Local Execution

```bash
uv venv
source .venv/bin/activate

uv pip install -e .[dev,test]

pytest
jupyter notebook
```

## General Notes

- This project requires Python >= 3.12
- Some dependencies were updated to ensure compatibility
- Since the code was run on a Mac, OpenMP had to be installed for xgboost dependency
