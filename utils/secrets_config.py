from __future__ import annotations


def _require_section(section: str) -> dict:
    import streamlit as st

    if section not in st.secrets:
        raise KeyError("missing")
    return dict(st.secrets[section])


def load_pricing_config() -> tuple[dict, dict]:
    alloy = _require_section("alloy")
    items = _require_section("items")
    return alloy, items
