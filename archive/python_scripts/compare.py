import sys

def load_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f]

file1, file2 = sys.argv[1], sys.argv[2]

a = load_lines(file1)
b = load_lines(file2)

print(f"Comparing:\n{file1}\n{file2}\n")
print(f"Total lines: {len(a)} vs {len(b)}\n")

max_len = max(len(a), len(b))
diff_count = 0

for i in range(max_len):
    l1 = a[i] if i < len(a) else "<MISSING>"
    l2 = b[i] if i < len(b) else "<MISSING>"

    if l1 != l2:
        diff_count += 1
        print(f"\n=== LINE {i+1} DIFFERENCE ===")
        print(f"FILE1: {l1}")
        print(f"FILE2: {l2}")

print(f"\nTotal differing lines: {diff_count}")