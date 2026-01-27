# Challenge

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
