import subprocess
import sys


def test_server_does_not_import_ml_stack():
    """El servidor tiene que arrancar sin pandas/sklearn: es lo que lo mantiene en ~60 MB en Railway."""
    code = "import sys, app.main; print(','.join(m for m in ('pandas', 'sklearn', 'numpy') if m in sys.modules))"
    loaded = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout.strip()
    assert loaded == ""
