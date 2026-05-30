import hashlib
import re

class Symbol(str): pass

def parse(program):
    """Parses S-expressions into nested lists of Symbols."""
    tokens = re.findall(r'\(|\)|[^\s()]+', program)
    def read_from_tokens(tokens):
        if not tokens: return None
        token = tokens.pop(0)
        if token == '(':
            lst = []
            while tokens[0] != ')':
                lst.append(read_from_tokens(tokens))
            tokens.pop(0) # pop ')'
            return lst
        else:
            try: return int(token)
            except ValueError: return Symbol(token)
    return read_from_tokens(tokens)

class AITRuntime:
    """The next-gen AIT-Lisp Evaluator with Content-Addressed Functions."""
    def __init__(self):
        self.store = {} # Hash -> Function/AST
        self.env = {
            's': self._security_domain,
            'm': self._memory_domain,
            'echo': lambda x: print(f"[ECHO] {x}")
        }
        self.corruption = 0

    def _security_domain(self, ctx_id, action, priority):
        """Native S-domain implementation."""
        print(f"--- [SEC] Executing Action '{action}' on Ctx {ctx_id} (P:{priority}) ---")
        if priority > 8:
            # Simulate an algebraic effect: Ask the OS if we should allow high-priority SEC
            yield ("EFFECT_AUTH_REQ", {"ctx": ctx_id, "action": action})
        return f"SEC_RESULT_{action}"

    def _memory_domain(self, ctx_id, action, priority):
        print(f"--- [MEM] {action} on {ctx_id} ---")
        return f"MEM_OK"

    def register_function(self, name, ast):
        """Registers a function and returns its Unison-style content hash."""
        code_str = str(ast)
        h = hashlib.sha256(code_str.encode()).hexdigest()[:12]
        self.store[h] = ast
        self.env[name] = h
        print(f"[STORE] Registered '{name}' as #{h}")
        return h

    def eval(self, x):
        """Evaluates an AIT-Lisp expression."""
        if isinstance(x, Symbol):
            # Content-Addressing: If it starts with '#', look up in store
            if x.startswith('#'):
                h = x[1:]
                if h in self.store: return self.store[h]
                raise Exception(f"Hash not found in store: {h}")

            val = self.env.get(x, x)
            # If the resolved value is a hash, look it up
            if isinstance(val, str) and val in self.store:
                return self.store[val]
            return val
        elif not isinstance(x, list):
            return x
        
        if not x: return None # Empty list

        # Function call: (fn arg1 arg2 ...)
        fn_sym = x[0]
        # Resolve the function part first
        fn = self.eval(fn_sym)
        
        # Evaluate arguments
        args = [self.eval(arg) for arg in x[1:]]
        
        if callable(fn):
            # Native Python function
            result = fn(*args)
            return result
        elif isinstance(fn, list):
            # S-expression function (Recursively evaluate)
            # This is the heart of Lisp: ( (s 4 x 9) ) is valid
            return self.eval(fn)
        else:
            raise Exception(f"Not a function: {fn_sym} -> {fn}")

def run_os_loop(runtime, program):
    """The 'Kernel' loop that handles algebraic effects (Yields)."""
    ast = parse(program)
    process = runtime.eval(ast)
    
    if hasattr(process, '__iter__') and not isinstance(process, (list, str, dict)):
        try:
            effect = next(process)
            print(f"[OS_KERNEL] Intercepted Effect: {effect[0]} -> {effect[1]}")
            # Decision: Always allow in this prototype, but resume the process
            # This is where Koka-style RESUME happens!
            try:
                process.send("AUTHORIZED")
            except StopIteration as e:
                return e.value
        except StopIteration as e:
            return e.value
    else:
        return process

if __name__ == "__main__":
    rt = AITRuntime()
    print("=== AIT-Lisp v0.1: Initializing... ===")
    
    # Example 1: Native call
    print("\nTest 1: Native AIT Execution")
    run_os_loop(rt, "(s 4 x 9)")
    
    # Example 2: Content-Addressed call
    print("\nTest 2: Unison-style Store")
    h = rt.register_function("custom-sec", parse("(s 1 verify 5)"))
    run_os_loop(rt, f"(#{h})") # Calling by hash
