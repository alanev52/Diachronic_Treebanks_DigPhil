import csv
import os
import json
import argparse

SUBORDINATE = {"acl", "ccomp", "advcl", "csubj"}

def load_confusion_matrix(path):
    matrix = {}
    with open(path, newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)[1:]  # predicted labels
        for row in reader:
            gold = row[0]
            counts = list(map(int, row[1:]))
            matrix[gold] = dict(zip(header, counts))
    return matrix

def compute_adjusted_accuracy(matrix):
    correct = 0
    total = 0

    for gold, preds in matrix.items():
        for pred, count in preds.items():
            total += count

            # exact match
            if gold == pred:
                correct += count

            # subordinate ↔ subordinate counts as correct
            elif gold in SUBORDINATE and pred in SUBORDINATE:
                correct += count

    return correct / total if total > 0 else 0.0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compute adjusted accuracy for all TSV confusion matrices in a folder."
    )
    parser.add_argument("folder", help="Folder containing TSV confusion matrix files")
    parser.add_argument(
        "--output", "-o", default="scores.json",
        help="Output JSON file to save scores (default: scores.json)"
    )
    args = parser.parse_args()

    folder = args.folder
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid directory")
        
    scores = {}
    folder = "./dep_rel/reparsed_stanza"
    for i,filename in enumerate(os.listdir(folder)):
        if filename.endswith(".tsv"):
            path = os.path.join(folder, filename)
            
            conf_matrix = load_confusion_matrix(path)
            score = compute_adjusted_accuracy(conf_matrix)
            print(f"Adjusted accuracy (ignoring subordinate confusions): {score:.4f}")
            scores[i]=round(score, 4)
    parser = folder.split('/')[-1]
    with open(f"scores_{parser}.json", "w") as f:
        print(f'outputing {f.name}')
        json.dump(scores, f, indent=4)