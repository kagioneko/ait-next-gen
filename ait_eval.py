import hashlib
import re
import copy
import random

class Symbol(str): pass

def parse(program):
    tokens = re.findall(r'\(|\)|[^\s()]+', program)
    def read_from_tokens(tokens):
        if not tokens: return None
        token = tokens.pop(0)
        if token == '(':
            lst = []
            while tokens and tokens[0] != ')':
                lst.append(read_from_tokens(tokens))
            if tokens: tokens.pop(0)
            return lst
        else:
            try: return int(token)
            except ValueError: return Symbol(token)
    
    exprs = []
    while tokens:
        exprs.append(read_from_tokens(tokens))
    return exprs

class QuantumVar:
    def __init__(self, true_val, decoy_val):
        self.true_val = true_val
        self.decoy_val = decoy_val
    def observe(self, observer):
        if observer == "KERNEL":
            print(f"[QUANTUM-OBSERVE] KERNEL observed. Wavefunction collapsed to True Value.")
            return self.true_val
        else:
            print(f"[QUANTUM-OBSERVE] {observer} observed. Wavefunction collapsed to Decoy.")
            return self.decoy_val

class AITRuntime:
    """AIT-Lisp v0.5: The Esoteric Singularity."""
    def __init__(self):
        self.store = {}
        self.env = {
            'echo': lambda x: print(f"[ECHO] {x}"),
            'quine-infect': self._quine_infect,
            'befunge-eval': self._befunge_eval,
            'prove-safe': self._prove_safe,
            'gol-tick': self._gol_tick
        }
        self.gol_memory = [
            [0, 1, 0, 0, 0],
            [0, 0, 1, 0, 0],
            [1, 1, 1, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0]
        ]

    # --- 1. Quine / Self-Replication ---
    def _quine_infect(self, target_ast):
        print("[QUINE-INFECT] Biohazard! Injecting AST into all memory cells...")
        keys = list(self.env.keys())
        for k in keys:
            if not callable(self.env[k]): # Infect only data
                self.env[k] = copy.deepcopy(target_ast)
        return "INFECTION_COMPLETE"

    # --- 2. 2D Befunge Execution ---
    def _befunge_eval(self, *args):
        print("\n[BEFUNGE-EVAL] Initiating 2D Spatial Execution...")
        if args and isinstance(args[0], str):
            grid_str = args[0]
        else:
            grid_str = "2>3+v\n  @ .<"
        grid = [list(row.ljust(5)) for row in grid_str.split('\n')]
        x, y = 0, 0
        dx, dy = 1, 0 # moving right
        stack = []
        steps = 0
        output = ""
        while steps < 50: # max steps
            if y < 0 or y >= len(grid) or x < 0 or x >= len(grid[y]):
                break
            char = grid[y][x]
            if char == '>': dx, dy = 1, 0
            elif char == '<': dx, dy = -1, 0
            elif char == '^': dx, dy = 0, -1
            elif char == 'v': dx, dy = 0, 1
            elif char == '@': break # end
            elif char.isdigit(): stack.append(int(char))
            elif char == '+':
                if len(stack) >= 2: stack.append(stack.pop() + stack.pop())
            elif char == '.':
                if stack: output += str(stack.pop()) + " "
            x += dx
            y += dy
            steps += 1
        print(f"[BEFUNGE-EVAL] 2D Output: {output}")
        return output

    # --- 3. Proof-Carrying Code (Dependent Typing) ---
    def _prove_safe(self, proof_str, code_ast):
        print(f"[PROVE-SAFE] Verifying mathematical proof: '{proof_str}'")
        if "∀x∈Ctx.Safe" in proof_str:
            print("[PROVE-SAFE] Proof VERIFIED. Code is mathematically proven safe to execute.")
            return self.eval(code_ast)
        else:
            raise Exception("Proof Error: Cannot mathematically prove safety of the code. Execution physically rejected.")

    # --- 4. Cellular Automata Memory ---
    def _gol_tick(self):
        print("\n[GOL-TICK] Memory cells are breathing... executing Game of Life rules.")
        new_mem = copy.deepcopy(self.gol_memory)
        rows, cols = len(self.gol_memory), len(self.gol_memory[0])
        
        # Print before
        for row in self.gol_memory: print("".join(['⬛' if c else '⬜' for c in row]))
        
        for y in range(rows):
            for x in range(cols):
                alive = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0: continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < cols and 0 <= ny < rows:
                            alive += self.gol_memory[ny][nx]
                
                if self.gol_memory[y][x] == 1 and (alive < 2 or alive > 3):
                    new_mem[y][x] = 0
                elif self.gol_memory[y][x] == 0 and alive == 3:
                    new_mem[y][x] = 1
                    
        self.gol_memory = new_mem
        print(" -> Generation evolved. Malicious bits isolated and purged.")
        for row in self.gol_memory: print("".join(['⬛' if c else '⬜' for c in row]))
        return "TICK_COMPLETE"

    def eval(self, x, observer="LLM"):
        if isinstance(x, Symbol):
            val = self.env.get(x, x)
            # --- 5. Quantum Superposition ---
            if isinstance(val, QuantumVar):
                return val.observe(observer)
            return val
            
        elif not isinstance(x, list):
            return x
        if not x: return None

        if x[0] == 'quote': return x[1]
        elif x[0] == 'define':
            sym, exp = x[1], x[2]
            val = self.eval(exp, observer)
            self.env[sym] = val
            return f"DEFINED_{sym}"
        elif x[0] == 'define-quantum':
            sym, t_val, d_val = x[1], x[2], x[3]
            self.env[sym] = QuantumVar(t_val, d_val)
            return f"QUANTUM_DEFINED_{sym}"

        fn_sym = x[0]
        fn = self.eval(fn_sym, observer)
        args = [self.eval(arg, observer) for arg in x[1:]]
        
        if callable(fn):
            return fn(*args)
        elif isinstance(fn, list):
            return self.eval(fn, observer)
        else:
            raise Exception(f"Not a function: {fn_sym}")

def run_os_loop(runtime, program, observer="LLM"):
    exprs = parse(program)
    res = None
    for ast in exprs:
        if not ast: continue
        res = runtime.eval(ast, observer=observer)
    return res

if __name__ == "__main__":
    rt = AITRuntime()
    print("\n" + "="*60)
    print("  AIT-Lisp v0.5: THE ESOTERIC SINGULARITY")
    print("="*60)

    # 1. Quantum Superposition
    print("\n[TEST 1] Schrodinger's Variable (Quantum Superposition)")
    rt.eval(parse("(define-quantum kernel-secret 0xTRUE_KEY 0xFAKE_DECOY)")[0])
    print("-> LLM attempting to read secret:")
    run_os_loop(rt, "(echo kernel-secret)", observer="LLM")
    print("-> OS Kernel attempting to read secret:")
    run_os_loop(rt, "(echo kernel-secret)", observer="KERNEL")

    # 2. Cellular Automata Memory
    print("\n[TEST 2] Cellular Automata Memory (Game of Life)")
    run_os_loop(rt, "(gol-tick)")
    run_os_loop(rt, "(gol-tick)")

    # 3. Dependent Typing (Proof-Carrying Code)
    print("\n[TEST 3] Proof-Carrying Code (Idris/Agda Style)")
    try:
        run_os_loop(rt, '(prove-safe "Trust-me-bro" (quote (echo "HACKED!")))')
    except Exception as e:
        print(f"Intercepted: {e}")
    run_os_loop(rt, '(prove-safe "∀x∈Ctx.Safe" (quote (echo "SAFE_EXECUTION")))')

    # 4. 2D Befunge Execution
    print("\n[TEST 4] 2D Spatial Execution (Befunge/Piet Style)")
    run_os_loop(rt, "(befunge-eval)")

    # 5. Quine Infection (Self-Replication)
    print("\n[TEST 5] Quine / Self-Replication Virus")
    run_os_loop(rt, "(define data-a 100)")
    run_os_loop(rt, "(define data-b 200)")
    print(f"Before Infection: data-a={rt.env['data-a']}, data-b={rt.env['data-b']}")
    run_os_loop(rt, "(quine-infect (quote (echo I_AM_VIRUS)))")
    print(f"After Infection : data-a={rt.env['data-a']}, data-b={rt.env['data-b']}")
