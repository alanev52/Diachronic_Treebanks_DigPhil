import sys

def find_multi_root_sentences(filepath):
    with open(filepath, encoding="utf-8") as f:
        sentence_lines = []
        sent_id = None
        root_by_head = []   # tokens where HEAD == 0
        root_by_deprel = [] # tokens where DEPREL == root
        found_any = False

        def check_and_print():
            nonlocal found_any
            if len(root_by_head) >= 2 or len(root_by_deprel) >= 2:
                found_any = True
                print(f"\n{'='*60}")
                if sent_id:
                    print(sent_id)
                print(f"Tokens with HEAD=0:    {root_by_head}")
                print(f"Tokens with DEPREL=root: {root_by_deprel}")
                print("\n".join(sentence_lines))

        for line in f:
            line = line.rstrip("\n")

            if line.startswith("# sent_id"):
                sent_id = line

            if line and not line.startswith("#"):
                fields = line.split("\t")
                if len(fields) >= 8 and "-" not in fields[0] and "." not in fields[0]:
                    token_id = fields[0]
                    head     = fields[6]
                    deprel   = fields[7].lower()
                    if head == "0":
                        root_by_head.append(token_id)
                    if deprel == "root" or deprel.startswith("root:"):
                        root_by_deprel.append(token_id)
                sentence_lines.append(line)

            elif line == "":
                check_and_print()
                sentence_lines = []
                sent_id = None
                root_by_head = []
                root_by_deprel = []

        # Handle file not ending with blank line
        check_and_print()

        if not found_any:
            print("No multi-root sentences found.")

if __name__ == "__main__":
    find_multi_root_sentences(sys.argv[1])