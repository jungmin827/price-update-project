"""Loader for domain scraping rules.

This is a minimal loader that will later be wired to Sheets via the
SheetsClient. For now it contains helper utilities and a simple in-memory
representation.
"""
from typing import Dict, List


class RulesStore:
    def __init__(self):
        self.rules: Dict[str, Dict] = {}

    def add_rule(self, domain_pattern: str, rule: Dict) -> None:
        self.rules[domain_pattern] = rule

    def get_rule_for_domain(self, domain: str) -> Dict:
        # simple substring match
        candidates = [d for d in self.rules.keys() if d in domain]
        if candidates:
            candidates.sort(key=len, reverse=True)
            return self.rules[candidates[0]]
        return self.rules.get("DEFAULT", {})

