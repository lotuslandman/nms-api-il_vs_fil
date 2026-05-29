import sys

f = '/home/scott/Documents/FAA/nms-monitor/src/reporting/analyze_matrix.py'
with open(f, 'r') as file:
    lines = file.readlines()

out = []
in_main = False
skip_auto_block = False

indent_rest = False
for line in lines:
    if line.startswith("def main():"):
        out.append(line)
        in_main = True
        continue
    
    if in_main:
        if "if len(sys.argv) > 1 and sys.argv[1] == '--auto':" in line:
            # Inject new loop logic
            out.append("""    import sys
    is_auto = len(sys.argv) > 1 and sys.argv[1] == '--auto'
    if is_auto:
        def is_cron_batch(b):
            try:
                time_part = b.split('_')[1]
                minute = int(time_part[2:4])
                hour = int(time_part[0:2])
                return minute in (0, 1) and hour % 2 == 0
            except:
                return False
        all_batches = [d for d in os.listdir(normalized_base) if os.path.isdir(os.path.join(normalized_base, d)) and is_cron_batch(d)]
        all_batches.sort(reverse=True)
        target_batches = all_batches[:3]
        max_examples = 50
    else:
        batch_id = select_batch(normalized_base)
        if not batch_id: return
        target_batches = [batch_id]
        max_examples = IntPrompt.ask("Enter maximum number of examples to show per category (0 for summaries only)", default=10)

    for batch_id in target_batches:
""")
            skip_auto_block = True
            continue
            
        if skip_auto_block:
            if line.strip() == 'batch_dir = os.path.join(normalized_base, batch_id)':
                skip_auto_block = False
                indent_rest = True
            continue
            
        if indent_rest and not line.startswith("if __name__ =="):
            out.append("    " + line if line.strip() else line)
        else:
            out.append(line)
            if line.startswith("if __name__ =="):
                indent_rest = False
    else:
        out.append(line)

with open(f, 'w') as file:
    file.writelines(out)

print("analyze_matrix.py updated successfully")
