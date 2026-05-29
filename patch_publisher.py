import sys

f = '/home/scott/Documents/FAA/nms-monitor/src/reporting/publish_to_pages.py'
with open(f, 'r') as file:
    c = file.read()

new_main = """def main():
    # 1. Ensure the destination directory exists
    if not os.path.exists(REPORTS_DEST_DIR):
        os.makedirs(REPORTS_DEST_DIR)

    # 2. Get recent batches and copy them over
    recent_batches = get_recent_cron_batches(3)
    if not recent_batches:
        print("No cron batches found in archives.")
    else:
        print(f"Copying recent batches: {recent_batches}")
        
        for i, batch in enumerate(recent_batches):
            opt3_filename = f"{batch}_matrix_report.html"
            opt3_src = os.path.join(OPT3_DIR, opt3_filename)
            opt3_dest = os.path.join(REPORTS_DEST_DIR, opt3_filename)
            if os.path.exists(opt3_src):
                shutil.copy2(opt3_src, opt3_dest)
                
            if i > 0:
                newer_batch = recent_batches[i-1]
                opt5_folder = f"{newer_batch}_to_{batch}"
                opt5_filename = f"report_fil_vs_nms-api_{newer_batch}_to_{batch}.html"
                opt5_src = os.path.join(OPT5_DIR, opt5_folder, opt5_filename)
                opt5_dest = os.path.join(REPORTS_DEST_DIR, opt5_filename)
                if os.path.exists(opt5_src):
                    shutil.copy2(opt5_src, opt5_dest)

    # 3. Gather ALL accumulated batches from the reports directory
    all_html_files = glob.glob(os.path.join(REPORTS_DEST_DIR, '*_matrix_report.html'))
    all_batches = []
    for f in all_html_files:
        filename = os.path.basename(f)
        b_id = filename.replace('_matrix_report.html', '')
        all_batches.append(b_id)
        
    all_batches.sort(reverse=True)
    if not all_batches:
        print("No accumulated batches to publish.")
        return
        
    print(f"Total accumulated batches to publish: {len(all_batches)}")

    # 4. Build index.html data
    rows_html = ""
    for i, batch in enumerate(all_batches):
        opt3_filename = f"{batch}_matrix_report.html"
        has_opt3 = os.path.exists(os.path.join(REPORTS_DEST_DIR, opt3_filename))
            
        opt5_link_html = "<!-- Empty, as there is no newer batch to compare to -->"
        
        if i > 0:
            newer_batch = all_batches[i-1]
            opt5_filename = f"report_fil_vs_nms-api_{newer_batch}_to_{batch}.html"
            
            if os.path.exists(os.path.join(REPORTS_DEST_DIR, opt5_filename)):
                time_newer = format_date(newer_batch).split(', ')[1]
                time_older = format_date(batch).split(', ')[1]
                
                opt5_link_html = f\"\"\"
       <div class="card card-opt5 staggered-up">
         <div class="date date-delta">Comparison: {time_newer} vs {time_older}</div>
         <a href="reports/{opt5_filename}">▶ Persistent Report</a>
       </div>\"\"\"
        
        date_str = format_date(batch)
        opt3_link = f'<a href="reports/{opt3_filename}">▶ Matrix Report</a>' if has_opt3 else '<span>Matrix Report Unavailable</span>'
        
        row_html = f\"\"\"
  <div class="timeline-row">
    <div class="col-left">
      <div class="card card-opt3">
        <div class="date">{date_str}</div>
        {opt3_link}
      </div>
    </div>
    <div class="col-right">
      {opt5_link_html}
    </div>
  </div>\"\"\"
        rows_html += row_html

    # 5. Generate index.html
    index_html = f\"\"\"<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>NMS Monitor Reports</title>
<style>
  body {{ font-family: monospace; background: #111; color: #eee; line-height: 1.5; }}
  .container {{ max-width: 900px; margin: 40px auto; }}
  h1 {{ color: #00afff; text-align: center; border-bottom: 2px solid #333; padding-bottom: 15px; margin-bottom: 40px; }}
  
  /* The Timeline Row */
  .timeline-row {{ display: flex; margin-bottom: 30px; }}
  
  /* Left Column: Option 3 (Single Batch) */
  .col-left {{ 
    flex: 1; 
    text-align: right; 
    padding-right: 30px; 
    border-right: 3px solid #444; 
    position: relative;
  }}
  
  /* Right Column: Option 5 (Comparison) */
  .col-right {{ 
    flex: 1; 
    padding-left: 30px; 
    position: relative; 
  }}
  
  /* Card Styling */
  .card {{ padding: 15px; border-radius: 6px; display: inline-block; text-align: left; min-width: 280px; }}
  .card-opt3 {{ background: #1a1a1a; border: 1px solid #444; }}
  .card-opt5 {{ background: #0c2a4d; border: 1px solid #1a5296; }}
  
  /* Staggering the right column upwards by half a row */
  .staggered-up {{ position: absolute; top: -50px; }}

  /* Node dots on the timeline */
  .col-left::after {{
    content: ''; position: absolute; right: -8px; top: 20px;
    width: 13px; height: 13px; background: #00afff; border-radius: 50%;
  }}

  /* Typography */
  .date {{ font-weight: bold; color: #cbd5e0; margin-bottom: 8px; font-size: 1.1em; }}
  .date-delta {{ color: #90cdf4; font-size: 0.9em; }}
  a {{ color: #63b3ed; text-decoration: none; font-weight: bold; }}
  a:hover {{ text-decoration: underline; color: #90cdf4; }}
</style>
</head>
<body>

<div class="container">
  <h1>NMS Monitor Reports</h1>
  {rows_html}
</div>
</body>
</html>
\"\"\"
    
    index_path = os.path.join(PAGES_REPO_DIR, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
        
    print(f"Generated {index_path}")

    # 6. Git commit and push
    print("Committing and pushing to GitHub Pages...")
    try:
        subprocess.run(['git', 'add', '.'], cwd=PAGES_REPO_DIR, check=True)
        status = subprocess.run(['git', 'status', '--porcelain'], cwd=PAGES_REPO_DIR, capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(['git', 'commit', '-m', 'Auto-published new reports'], cwd=PAGES_REPO_DIR, check=True)
            subprocess.run(['git', 'push'], cwd=PAGES_REPO_DIR, check=True)
            print("Successfully published to GitHub Pages.")
        else:
            print("No changes to publish.")
    except Exception as e:
        print(f"Failed to publish to git: {e}")
"""

# Replace the existing main function
start_idx = c.find('def main():')
c = c[:start_idx] + new_main

with open(f, 'w') as file:
    file.write(c)

print("publish_to_pages.py updated successfully")
