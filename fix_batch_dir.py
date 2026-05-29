import sys

f = '/home/scott/Documents/FAA/nms-monitor/src/reporting/analyze_matrix.py'
with open(f, 'r') as file:
    c = file.read()

target = '    for batch_id in target_batches:\n\n    \n        rprint(f"\\n[bold cyan]Analyzing Batch {batch_id}...[/bold cyan]\\n")\n    \n        fil_files = glob.glob(os.path.join(batch_dir, \'*_fil.parquet\'))'
replacement = '    for batch_id in target_batches:\n        batch_dir = os.path.join(normalized_base, batch_id)\n    \n        rprint(f"\\n[bold cyan]Analyzing Batch {batch_id}...[/bold cyan]\\n")\n    \n        fil_files = glob.glob(os.path.join(batch_dir, \'*_fil.parquet\'))'

c = c.replace(target, replacement)

with open(f, 'w') as file:
    file.write(c)

print("Fixed batch_dir in analyze_matrix.py")
