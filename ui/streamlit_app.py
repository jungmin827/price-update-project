"""Minimal Streamlit UI to trigger a run and show basic status.

Requires streamlit to be installed. This file is intentionally small and
calls into the project's CLI/runner in a subprocess for simplicity.
"""
import subprocess
import streamlit as st

st.title("PriceBot Control Panel")
if st.button("Run once now"):
    # Call CLI entrypoint; this assumes `python -m project.cli` is available.
    result = subprocess.run(["python3", "-m", "project.cli"], capture_output=True, text=True)
    st.text_area("Output", result.stdout + "\n" + result.stderr, height=300)

st.write("Use this UI to start ad-hoc runs. For production, wire a proper API.")

