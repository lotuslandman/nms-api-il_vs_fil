import sys
import os
import re

base = "/home/scott/Documents/FAA/nms-monitor/src"

# 1. Modify compare_services.py
f_compare = f"{base}/reporting/compare_services.py"
with open(f_compare, "r") as f: content = f.read()

# Update get_html_block calls with colored count
content = re.sub(
    r'html_sections\.append\(get_html_block\(([^,]+),\s*title=f"Examples:\s*\{status\}"\)\)',
    r'html_sections.append(get_html_block(\1, title=f"Examples: {status} <span style=\'color: cyan;\'>({count:,})</span>"))',
    content
)
content = re.sub(
    r'outlier_html_sections\.append\(get_html_block\(([^,]+),\s*title=f"Outliers:\s*\{b\[\'category\'\]\}\s*\(\{sys_val\}\)"\)\)',
    r'outlier_html_sections.append(get_html_block(\1, title=f"Outliers: {b[\'category\']} ({sys_val}) <span style=\'color: {st.replace(\"bold \", \"\")};\'>({total_pairs:,})</span>"))',
    content
)
content = re.sub(
    r'outlier_html_sections\.append\(get_html_block\(([^,]+),\s*title=f"Outliers:\s*\{html_title\}"\)\)',
    r'outlier_html_sections.append(get_html_block(\1, title=f"Outliers: {html_title} <span style=\'color: {st.replace(\"bold \", \"\")};\'>({b[\"count\"]:,})</span>"))',
    content
)

with open(f_compare, "w") as f: f.write(content)

# 2. Modify analyze_matrix.py
f_matrix = f"{base}/reporting/analyze_matrix.py"
with open(f_matrix, "r") as f: content = f.read()

# Top two tables non-collapsible
content = content.replace(
    'html_sections.append(get_html_block(p0, title="Input Data & Artifacts"))',
    'html_sections.append(get_html_block(p0))'
)
content = content.replace(
    'html_sections.append(get_html_block(p1, title="System vs. Classification"))',
    'html_sections.append(get_html_block(p1))'
)
content = content.replace(
    'html_sections.append(get_html_block(p3, title="Key Uniqueness Summary"))',
    'html_sections.append(get_html_block(p3))'
)

# ID Uniqueness non-collapsible summary, collapsible details
content = content.replace(
    'id_renderables.append(t2a)',
    'console.print(t2a)\n    html_sections.append(get_html_block(t2a))\n    # id_renderables.append(t2a)'
)
content = content.replace(
    'html_sections.append(get_html_block(p2, title="ID Uniqueness & Discrepancies"))',
    '# html_sections.append(get_html_block(p2, title="ID Uniqueness & Discrepancies"))'
)

# Update HTML titles for tables in loops
content = re.sub(
    r'id_renderables\.append\(t\)',
    r'html_sections.append(get_html_block(t, title=f"Non-Standard NMS IDs: {s[\'System\']} <span style=\'color: red;\'>({s[\'Non-Standard IDs\']:,})</span>"))\n                id_renderables.append(t)',
    content, count=1
)

content = re.sub(
    r'id_renderables\.append\(t\)',
    r'html_sections.append(get_html_block(t, title=f"Duplicate NOTAM IDs: {s[\'System\']} <span style=\'color: red;\'>({total_id_rows:,})</span>"))\n                id_renderables.append(t)',
    content, count=1
)

content = re.sub(
    r'html_sections\.append\(get_html_block\(te, title=f"Discrepancies: \{cat\}"\)\)',
    r'html_sections.append(get_html_block(te, title=f"Discrepancies: {cat} <span style=\'color: red;\'>({total_count:,})</span>"))',
    content
)

content = re.sub(
    r'nof_renderables\.append\(t\)',
    r'html_sections.append(get_html_block(t, title=f"UNKNOWN NOF Examples: {s[\'System\']} <span style=\'color: red;\'>({s[\'Unknown NOF Count\']:,})</span>"))\n                nof_renderables.append(t)',
    content, count=1
)
content = content.replace(
    'html_sections.append(get_html_block(p4, title="Unknown NOF Analysis"))',
    '# html_sections.append(get_html_block(p4, title="Unknown NOF Analysis"))'
)
content = content.replace(
    'nof_renderables.append(t_nof_summary)',
    'console.print(t_nof_summary)\n    html_sections.append(get_html_block(t_nof_summary))'
)

# Modify main() in analyze_matrix.py to support --auto
main_auto_matrix = """def main():
    normalized_base = 'data/normalized'
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        batches = [d for d in os.listdir(normalized_base) if os.path.isdir(os.path.join(normalized_base, d))]
        batches.sort(reverse=True)
        if not batches: return
        batch_id = batches[0]
        max_examples = 50
    else:
        batch_id = select_batch(normalized_base)
        if not batch_id: return
        max_examples = IntPrompt.ask("Enter maximum number of examples to show per category (0 for summaries only)", default=10)
"""
content = re.sub(r'def main\(\):\n\s+normalized_base = \'data/normalized\'\n\s+batch_id = select_batch\(normalized_base\)\n\s+if not batch_id: return\n\s+batch_dir = os.path.join\(normalized_base, batch_id\)\n\s+max_examples = IntPrompt.ask\("Enter maximum number of examples to show per category \(0 for summaries only\)", default=10\)',
main_auto_matrix + "    batch_dir = os.path.join(normalized_base, batch_id)\n", content)

with open(f_matrix, "w") as f: f.write(content)

# 3. Modify persistent_comparisons.py for --auto
f_pers = f"{base}/reporting/persistent_comparisons.py"
with open(f_pers, "r") as f: content = f.read()

main_auto_pers_alt = """def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        service1 = "FIL"
        service2 = "NMS-API-IL"
        batches1 = get_successful_batches(service1)
        batches2 = get_successful_batches(service2)
        common_batches = sorted(list(batches1.intersection(batches2)), reverse=True)
        if len(common_batches) < 2: return
        b1 = common_batches[0]
        b2 = common_batches[1]
        max_examples = 50
        classification_only = False
        
        path_a_b1 = get_parquet_path(b1, service1)
        path_b_b1 = get_parquet_path(b1, service2)
        run_comparison(b1, path_a_b1, path_b_b1, max_examples=max_examples, classification_only=classification_only)
        
        path_a_b2 = get_parquet_path(b2, service1)
        path_b_b2 = get_parquet_path(b2, service2)
        run_comparison(b2, path_a_b2, path_b_b2, max_examples=max_examples, classification_only=classification_only)
        return
"""

content = content.replace("def main():", main_auto_pers_alt)
with open(f_pers, "w") as f: f.write(content)

# 4. Modify main.py to call these in active_load
f_main = f"{base}/main.py"
with open(f_main, "r") as f: content = f.read()

trigger_code = """
        # --- Run Reports ---
        try:
            import subprocess
            logger.info("Running Option 3 (Matrix) and Option 5 (Persistent Comparisons)...")
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            python_exe = sys.executable
            subprocess.run([python_exe, "src/reporting/analyze_matrix.py", "--auto"], cwd=base_dir, check=True)
            subprocess.run([python_exe, "src/reporting/persistent_comparisons.py", "--auto"], cwd=base_dir, check=True)
        except Exception as e:
            logger.error(f"Failed to run reports: {e}")

        logger.info(f"Active load process completed (Batch: {batch_id}).")
"""
content = content.replace('        logger.info(f"Active load process completed (Batch: {batch_id}).")', trigger_code)
with open(f_main, "w") as f: f.write(content)
print("Patch applied successfully")
