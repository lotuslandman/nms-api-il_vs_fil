import os
import glob
import re
from rich.console import Console
from rich.table import Table
from rich.prompt import IntPrompt
from rich import print as rprint
import sys
import pandas as pd

# Add project root to python path so we can import from src.reporting
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.reporting.compare_services import run_comparison, get_comparison_data, render_comparison_report
except ImportError as e:
    rprint(f"[bold red]Failed to import comparison functions: {e}[/bold red]")
    run_comparison = None
    get_comparison_data = None
    render_comparison_report = None

console = Console()

ARCHIVE_DIR = "data/archives"
NORMALIZED_DIR = "data/normalized"

# Service Name to File Pattern mapping
SERVICES = {
    "FIL": {"xml": "*_fil_il.xml", "parquet_suffix": "fil"},
    "NMS-API-IL": {"xml": "*_api_il.xml", "parquet_suffix": "nms-api"},
    "NMS-NDS": {"xml": "*_nds_il_*.xml", "parquet_suffix": "nms-nds"},
    "NMS-XMLQ": {"xml": "*_xmlq_*.xml", "parquet_suffix": "xml-query"}
}

def get_timestamp(batch_id):
    match = re.match(r'(\d{4}-\d{2}-\d{2}_\d{6}Z)', batch_id)
    return match.group(1) if match else batch_id

def get_successful_batches(service_name):
    pattern = SERVICES.get(service_name, {}).get("xml")
    if not pattern:
        return set()
    
    successful = set()
    if not os.path.exists(ARCHIVE_DIR):
        return successful

    for batch_dir in os.listdir(ARCHIVE_DIR):
        dir_path = os.path.join(ARCHIVE_DIR, batch_dir)
        if os.path.isdir(dir_path):
            files = glob.glob(os.path.join(dir_path, pattern))
            if files:
                successful.add(get_timestamp(batch_dir))
    return successful

def get_parquet_path(batch_id, service_name):
    suffix = SERVICES.get(service_name, {}).get("parquet_suffix")
    return os.path.join(NORMALIZED_DIR, batch_id, f"{batch_id}_{suffix}.parquet")

def run_persistent_report(service1, service2, batch1, batch2, max_examples):
    rprint("\n" + "═"*50)
    rprint(f" [bold red]PERSISTENT DISCREPANCIES DETAILED REPORT ({batch1} vs {batch2})[/bold red]")
    rprint("═"*50)
    
    extra_html = []
    if run_comparison:
        for batch in [batch1, batch2]:
            path_a = get_parquet_path(batch, service1)
            path_b = get_parquet_path(batch, service2)
            
            if not os.path.exists(path_a) or not os.path.exists(path_b):
                continue
                
            html_b = run_comparison(batch, path_a, path_b, max_examples=max_examples, classification_only=True)
            if html_b:
                extra_html.append(f"<h2 style='color: yellow;'>Classification Breakdown: Batch {batch}</h2>")
                extra_html.extend(html_b)
                
        label_a = SERVICES[service1]["parquet_suffix"]
        label_b = SERVICES[service2]["parquet_suffix"]
        
        path_a_1 = get_parquet_path(batch1, service1)
        path_b_1 = get_parquet_path(batch1, service2)
        ignore_id = ("fil" in label_a and "nms" in label_b) or ("nms" in label_a and "fil" in label_b)
        
        if os.path.exists(path_a_1) and os.path.exists(path_b_1) and \
           os.path.exists(get_parquet_path(batch2, service1)) and os.path.exists(get_parquet_path(batch2, service2)):
           
            int_1, out_a_1, out_b_1, fuzzy_1 = get_comparison_data(path_a_1, path_b_1, ignore_id)

            path_a_2 = get_parquet_path(batch2, service1)
            path_b_2 = get_parquet_path(batch2, service2)
            int_2, out_a_2, out_b_2, fuzzy_2 = get_comparison_data(path_a_2, path_b_2, ignore_id)

            int_1_keys = set(zip(int_1['notam_key'], int_1['match_status']))
            persistent_int = int_2[int_2.apply(lambda r: (r['notam_key'], r['match_status']) in int_1_keys, axis=1)].copy()

            persistent_out_a = out_a_2[out_a_2['notam_key'].isin(out_a_1['notam_key'])].copy()
            persistent_out_b = out_b_2[out_b_2['notam_key'].isin(out_b_1['notam_key'])].copy()

            persistent_fuzzy = fuzzy_2[fuzzy_2['notam_key_A'].isin(fuzzy_1['notam_key_A'])].copy()

            df_supp_full = pd.DataFrame()
            for b_id in [batch1, batch2]:
                b_dir = os.path.join(NORMALIZED_DIR, b_id)
                if os.path.exists(b_dir):
                    supp_file = next((f for f in os.listdir(b_dir) if f.endswith("_nms-api-supplemental.parquet")), None)
                    if supp_file:
                        df_supp = pd.read_parquet(os.path.join(b_dir, supp_file))
                        df_supp_full = pd.concat([df_supp_full, df_supp], ignore_index=True)
            
            if not df_supp_full.empty:
                df_supp_full = df_supp_full.drop_duplicates('notam_key')

            extra_html.append(f"<br><h2 style='color: yellow;'>Persistent Discrepancies Details ({batch1} vs {batch2})</h2>")

            render_comparison_report(
                batch_id=f"persistence/{batch1}_to_{batch2}", 
                batch_dir=None, 
                service_a_label=label_a, 
                service_b_label=label_b, 
                intersection=persistent_int, 
                orphans_a=persistent_out_a, 
                orphans_b=persistent_out_b, 
                fuzzy_matches=persistent_fuzzy, 
                ignore_id=ignore_id,
                max_examples=max_examples,
                df_supp_full=df_supp_full,
                extra_html_sections=extra_html
            )

def main():
    import sys
    is_auto = len(sys.argv) > 1 and sys.argv[1] == '--auto'
    service_list = list(SERVICES.keys())

    if is_auto:
        service1 = "FIL"
        service2 = "NMS-API-IL"
        
        def is_cron_batch(b):
            try:
                time_part = b.split('_')[1]
                minute = int(time_part[2:4])
                hour = int(time_part[0:2])
                return minute in (0, 1) and hour % 2 == 0
            except:
                return False

        batches1 = get_successful_batches(service1)
        batches2 = get_successful_batches(service2)
        common_batches = sorted(list(batches1.intersection(batches2)), reverse=True)
        cron_batches = [b for b in common_batches if is_cron_batch(b)]
        
        if len(cron_batches) < 2: return
        max_examples = 50
        
        # In auto mode, we do the most recent pair, and the next most recent pair if available
        pairs_to_run = []
        pairs_to_run.append((cron_batches[0], cron_batches[1]))
        if len(cron_batches) >= 3:
            pairs_to_run.append((cron_batches[1], cron_batches[2]))
            
        for b1, b2 in pairs_to_run:
            run_persistent_report(service1, service2, b1, b2, max_examples)
            
    else:
        # Manual Mode
        rprint("\n[bold]Step 1: Select Services[/bold]")
        table = Table(title="Available Services", show_header=True, header_style="bold magenta")
        table.add_column("Index", justify="right", style="cyan")
        table.add_column("Service", style="green")
        for i, name in enumerate(service_list):
            table.add_row(str(i+1), name)
        console.print(table)
        
        s1_idx = IntPrompt.ask("Select Service 1 index", choices=[str(i+1) for i in range(len(service_list))], default=1)
        s2_idx = IntPrompt.ask("Select Service 2 index", choices=[str(i+1) for i in range(len(service_list))], default=2)
        service1 = service_list[s1_idx - 1]
        service2 = service_list[s2_idx - 1]
        
        batches1 = get_successful_batches(service1)
        batches2 = get_successful_batches(service2)
        common_batches = sorted(list(batches1.intersection(batches2)), reverse=True)
        
        if not common_batches:
            rprint(f"\n[bold red]Error: No batches found that are successful for both {service1} and {service2}.[/bold red]")
            return

        rprint("\n[bold]Step 3: Select Batches[/bold]")
        batch_table = Table(title=f"Common Successful Batches", show_header=True, header_style="bold blue")
        batch_table.add_column("Index", justify="right", style="cyan")
        batch_table.add_column("Batch Timestamp", style="yellow")
        for i, batch in enumerate(common_batches):
            batch_table.add_row(str(i+1), batch)
        console.print(batch_table)
        
        b1_idx = IntPrompt.ask("Select Batch 1 index", choices=[str(i+1) for i in range(len(common_batches))], default=1)
        b2_default = 2 if len(common_batches) >= 2 else 1
        b2_idx = IntPrompt.ask("Select Batch 2 index", choices=[str(i+1) for i in range(len(common_batches))], default=b2_default)
        
        batch1 = common_batches[b1_idx - 1]
        batch2 = common_batches[b2_idx - 1]
        max_examples = IntPrompt.ask("Enter maximum number of examples to show per category (0 for summaries only)", default=10)
        
        run_persistent_report(service1, service2, batch1, batch2, max_examples)

if __name__ == "__main__":
    main()
