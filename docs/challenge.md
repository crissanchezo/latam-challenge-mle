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
