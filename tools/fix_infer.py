import re, subprocess, sys
for it in range(15):
    out = subprocess.run([r"C:\Godot\Godot_v4.4.1-stable_win64_console.exe","--headless","--path",".","--quit-after","30"],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    txt = out.stdout + out.stderr
    errs = re.findall(r'Cannot infer the type of "(\w+)" variable.*?\n\s+at: GDScript::reload \(res://([^:]+):(\d+)\)', txt)
    if not errs:
        other = [l for l in txt.splitlines() if 'SCRIPT ERROR' in l or ('ERROR' in l and 'leaked' not in l)]
        print("no infer errors; remaining:", "\n".join(sorted(set(other))[:40]))
        break
    fixed = 0
    for var, path, line in set(errs):
        ln = int(line)
        lines = open(path, encoding='utf-8').read().split('\n')
        if f'var {var} :=' in lines[ln-1]:
            lines[ln-1] = lines[ln-1].replace(f'var {var} :=', f'var {var} =', 1); fixed += 1
        else:
            print("could not fix", var, path, ln, lines[ln-1])
        open(path, 'w', encoding='utf-8').write('\n'.join(lines))
    print("iteration", it, "fixed", fixed)
