import sys, os
sys.stdout = open(os.path.join(os.path.dirname(__file__), 'server_output.txt'), 'w', encoding='utf-8')
sys.stderr = sys.stdout
print("Starting server...", flush=True)

try:
    exec(open(os.path.join(os.path.dirname(__file__), 'server.py'), encoding='utf-8').read())
except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
