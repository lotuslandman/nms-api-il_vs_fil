import os
import glob
import shutil
import re
import subprocess
from datetime import datetime

# Paths
NMS_MONITOR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
PAGES_REPO_DIR = '/home/scott/Documents/FAA/nms-api-il-vs-fil'
REPORTS_DEST_DIR = os.path.join(PAGES_REPO_DIR, 'reports')

ARCHIVE_DIR = os.path.join(NMS_MONITOR_DIR, 'data', 'archives')
OPT3_DIR = os.path.join(NMS_MONITOR_DIR, 'data', 'reports', 'duplicates')
OPT5_DIR = os.path.join(NMS_MONITOR_DIR, 'data', 'reports', 'comparisons', 'persistence')

def is_cron_batch(batch_id):
    try:
        time_part = batch_id.split('_')[1]
        minute = int(time_part[2:4])
        hour = int(time_part[0:2])
        return minute in (0, 1) and hour % 2 == 0
    except:
        return False

def get_recent_cron_batches(limit=3):
    if not os.path.exists(ARCHIVE_DIR):
        return []
    
    batches = []
    for d in os.listdir(ARCHIVE_DIR):
        if os.path.isdir(os.path.join(ARCHIVE_DIR, d)):
            # Check if it looks like a batch ID and is cron
            match = re.match(r'^(\d{4}-\d{2}-\d{2}_\d{6}Z)$', d)
            if match and is_cron_batch(d):
                batches.append(d)
                
    batches.sort(reverse=True)
    return batches[:limit]

def format_date(batch_id):
    # '2026-05-28_220001Z' -> 'May 28, 22:00Z'
    try:
        dt = datetime.strptime(batch_id, '%Y-%m-%d_%H%M%SZ')
        return dt.strftime('%B %d, %H:%MZ')
    except:
        return batch_id

def main():
    # 1. Clean the destination directory
    if os.path.exists(REPORTS_DEST_DIR):
        shutil.rmtree(REPORTS_DEST_DIR)
    os.makedirs(REPORTS_DEST_DIR)

    # 2. Get recent batches
    batches = get_recent_cron_batches(3)
    if not batches:
        print("No cron batches found to publish.")
        return

    print(f"Publishing batches: {batches}")

    # 3. Copy files and build index.html data
    rows_html = ""
    
    for i, batch in enumerate(batches):
        opt3_filename = f"{batch}_matrix_report.html"
        opt3_src = os.path.join(OPT3_DIR, opt3_filename)
        opt3_dest = os.path.join(REPORTS_DEST_DIR, opt3_filename)
        
        has_opt3 = False
        if os.path.exists(opt3_src):
            shutil.copy2(opt3_src, opt3_dest)
            has_opt3 = True
            
        opt5_link_html = "<!-- Empty, as there is no newer batch to compare to -->"
        
        # If this is not the newest batch (i=0), we can link to a comparison with the NEXT newest batch (i-1)
        # Wait, the visual concept shows the OPT5 box is placed on the ROW of the OLDER batch, floating up.
        # But actually in the loop, if we are at batch i, the comparison is between i-1 and i.
        # So we only have opt5 for i > 0.
        if i > 0:
            newer_batch = batches[i-1]
            opt5_folder = f"{newer_batch}_to_{batch}"
            opt5_filename = f"report_fil_vs_nms-api_{newer_batch}_to_{batch}.html"
            opt5_src = os.path.join(OPT5_DIR, opt5_folder, opt5_filename)
            opt5_dest = os.path.join(REPORTS_DEST_DIR, opt5_filename)
            
            if os.path.exists(opt5_src):
                shutil.copy2(opt5_src, opt5_dest)
                time_newer = format_date(newer_batch).split(', ')[1]
                time_older = format_date(batch).split(', ')[1]
                
                opt5_link_html = f"""
       <div class="card card-opt5 staggered-up">
         <div class="date date-delta">Comparison: {time_newer} vs {time_older}</div>
         <a href="reports/{opt5_filename}">▶ Persistent Report</a>
       </div>"""
        
        date_str = format_date(batch)
        opt3_link = f'<a href="reports/{opt3_filename}">▶ Matrix Report</a>' if has_opt3 else '<span>Matrix Report Unavailable</span>'
        
        row_html = f"""
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
  </div>"""
        rows_html += row_html

    # 4. Generate index.html
    index_html = f"""<!DOCTYPE html>
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
"""
    
    index_path = os.path.join(PAGES_REPO_DIR, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_html)
        
    print(f"Generated {index_path}")

    # 5. Git commit and push
    print("Committing and pushing to GitHub Pages...")
    try:
        subprocess.run(['git', 'add', '.'], cwd=PAGES_REPO_DIR, check=True)
        # Check if there are changes to commit
        status = subprocess.run(['git', 'status', '--porcelain'], cwd=PAGES_REPO_DIR, capture_output=True, text=True)
        if status.stdout.strip():
            subprocess.run(['git', 'commit', '-m', 'Auto-published new reports'], cwd=PAGES_REPO_DIR, check=True)
            subprocess.run(['git', 'push'], cwd=PAGES_REPO_DIR, check=True)
            print("Successfully published to GitHub Pages.")
        else:
            print("No changes to publish.")
    except Exception as e:
        print(f"Failed to publish to git: {e}")

if __name__ == "__main__":
    main()
