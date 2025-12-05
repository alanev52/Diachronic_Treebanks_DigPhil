import json
import os
import sys

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 json_to_table.py <json_file>")
        sys.exit(1)
    file = sys.argv[1]
    outfile = sys.argv[2]
    #if not os.path.exist(outfile):


    with open(file, "r") as f:
        with open(outfile, 'w') as of:
            data = json.load(f)

            of.write(f"{'Pattern':50} \t{'p_occs':>6} \t {'p_q_occs':>8} \t {'Decision':>8}\t {'Coef':>6}\t {'coverage':>6}\t {'precision':>6}\t {'cramers_phi':>6}\n")
            of.write("-"*120)
            of.write("\n")

            for rule in data["rules"]:
                pattern = rule["pattern"]
                p_occs = rule["p_occs"]
                p_q_occs = rule["p_q_occs"]
                decision = rule["decision"]
                coef = rule["coef"]
                coverage = rule["coverage"]
                precision = rule["precision"]
                cramers_phi = rule["cramers_phi"]
                of.write(f"{pattern:50}\t {p_occs:6}\t {p_q_occs:8}\t {decision:8}\t {coef:6.3f}\t {coverage:6.3f}\t {precision:6.2f}\t {cramers_phi:6.2f}\n")
            

if __name__ == "__main__":
    main()