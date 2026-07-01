PRODUCER_COLOR = "\033[93m"
SCREENWRITER_COLOR = "\033[96m"
DIRECTOR_COLOR = "\033[92m"
DIM = "\033[2m"
RESET = "\033[0m"


def banner(name, color):
    line = "=" * 55
    print(f"\n{color}{line}")
    print(f"  {name}")
    print(f"{line}{RESET}")


def thinking(name, color, text):
    print(f"{color}[{name}]: {text}{RESET}")


def result(name, color, text):
    print(f"{color}>>> {name}: {text}{RESET}")


def dim(text):
    print(f"{DIM}{text}{RESET}")
