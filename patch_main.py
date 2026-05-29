import sys

f = '/home/scott/Documents/FAA/nms-monitor/src/main.py'
with open(f, 'r') as file:
    c = file.read()

target = 'subprocess.run([python_exe, "src/reporting/persistent_comparisons.py", "--auto"], cwd=base_dir, check=True)'
replacement = target + '\n            logger.info("Publishing to GitHub Pages...")\n            subprocess.run([python_exe, "src/reporting/publish_to_pages.py"], cwd=base_dir, check=True)'

c = c.replace(target, replacement)

with open(f, 'w') as file:
    file.write(c)

print("main.py updated successfully")
