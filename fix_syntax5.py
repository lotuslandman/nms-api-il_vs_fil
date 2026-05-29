import sys

f = '/home/scott/Documents/FAA/nms-monitor/src/reporting/analyze_matrix.py'
with open(f, 'r') as file:
    c = file.read()

# The mistake was appending the duplicate string right after the non-standard one.
# It currently looks like:
# html_sections.append(get_html_block(t, title=f"Non-Standard NMS IDs: {s[\"System\"]} <span style='color: red;'>({s[\"Non-Standard IDs\"]:,})</span>"))
# html_sections.append(get_html_block(t, title=f"Duplicate NOTAM IDs: {s[\"System\"]} <span style='color: red;'>({total_id_rows:,})</span>"))
# id_renderables.append(t)

# Let's find this block and remove the second line.
wrong_string = "                html_sections.append(get_html_block(t, title=f\"Duplicate NOTAM IDs: {s[\\\"System\\\"]} <span style='color: red;'>({total_id_rows:,})</span>\"))\n"

c = c.replace(wrong_string, "")

# Now we need to add the duplicate HTML block line where it ACTUALLY belongs.
# It belongs in the loop: for s in stats: \n total_id_rows = len(s['id_dups_df'])
# down below, right before the SECOND id_renderables.append(t)

# The second loop has:
#                     text_snippet, simple_snippet
#                 )
#             id_renderables.append(t)
# We need to replace THAT id_renderables.append(t)

target = "                id_renderables.append(t)"
replacement = "                html_sections.append(get_html_block(t, title=f\"Duplicate NOTAM IDs: {s['System']} <span style='color: red;'>({total_id_rows:,})</span>\"))\n                id_renderables.append(t)"

# We replace the LAST occurrence of `id_renderables.append(t)`
parts = c.rsplit(target, 1)
if len(parts) == 2:
    c = parts[0] + replacement + parts[1]

with open(f, 'w') as file:
    file.write(c)
