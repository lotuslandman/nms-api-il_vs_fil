import os
import sys
import re

f = '/home/scott/Documents/FAA/nms-monitor/src/reporting/compare_services.py'
with open(f, 'r') as file:
    c = file.read()

# 1. Update render_comparison_report signature
c = c.replace(
    "def render_comparison_report(batch_id, batch_dir, service_a_label, service_b_label, intersection, orphans_a, orphans_b, fuzzy_matches, ignore_id, max_examples=10, classification_only=False, df_supp_full=None):",
    "def render_comparison_report(batch_id, batch_dir, service_a_label, service_b_label, intersection, orphans_a, orphans_b, fuzzy_matches, ignore_id, max_examples=10, classification_only=False, df_supp_full=None, extra_html_sections=None):"
)

# 2. Update html_sections initialization inside render_comparison_report
c = c.replace(
    "html_console = Console(record=True, width=225, force_terminal=True)\n    html_sections = []",
    "html_console = Console(record=True, width=225, force_terminal=True)\n    html_sections = extra_html_sections or []"
)

# 3. Update the return when classification_only
c = c.replace(
    "if classification_only:\n        return",
    "if classification_only:\n        return html_sections"
)

# 4. Update run_comparison to return what render_comparison_report returns
c = c.replace(
    "render_comparison_report(batch_id, batch_dir, service_a_label, service_b_label, intersection, orphans_a, orphans_b, fuzzy_matches, ignore_id, max_examples, classification_only, df_supp_full=None)",
    "return render_comparison_report(batch_id, batch_dir, service_a_label, service_b_label, intersection, orphans_a, orphans_b, fuzzy_matches, ignore_id, max_examples, classification_only, df_supp_full=None)"
)
# Just in case the exact call string above is slightly different, let's use regex
c = re.sub(
    r"(\n\s+)render_comparison_report\(batch_id, batch_dir, service_a_label, service_b_label, intersection, orphans_a, orphans_b, fuzzy_matches, ignore_id, max_examples, classification_only, df_supp_full=None\)",
    r"\1return render_comparison_report(batch_id, batch_dir, service_a_label, service_b_label, intersection, orphans_a, orphans_b, fuzzy_matches, ignore_id, max_examples, classification_only, df_supp_full=None)",
    c
)

with open(f, 'w') as file:
    file.write(c)

print("compare_services.py updated successfully")
