from mod_conll18_ud_eval import load_conllu, evaluate
from collections import defaultdict
import pyconll
import sys
import os
import numpy as np
import pandas as pd

def check_valid_gold(gold_file_path):
    """ Check that the gold trees are valid """
    gold_data = pyconll.load_from_file(gold_file_path)
    errors = []
    for sentence in gold_data:
        for token in sentence:
            if token.head is None:
                e = ValueError(f"Invalid gold tree in file {gold_file_path}, sentence ID {sentence.id}: token {token.id} '{token.form}' has no head.")
                errors.append(e)
            elif token.head == token.id:
                e = ValueError(f"Invalid gold tree in file {gold_file_path}, sentence ID {sentence.id}: token {token.id} '{token.form}' has itself as head.")
                errors.append(e)
        roots = [token for token in sentence if token.head == '0']
        if len(roots) != 1:
            e = ValueError(f"Invalid gold tree in file {gold_file_path}, sentence ID {sentence.id}: expected 1 root, found {len(roots)}.")
            errors.append(e)
    return errors if len(errors) > 0 else None

def preprocess_system_file(system_file_path, gold_file_path):
    """ Make a new base file with only the trees present in the gold file """
    gold_conllu = pyconll.load_from_file(gold_file_path)
    system_conllu = pyconll.load_from_file(system_file_path)
    gold_ids = {sentence.id for sentence in gold_conllu}
    filtered_sentences = [sentence for sentence in system_conllu if sentence.id in gold_ids]
    preprocessed_file_path = system_file_path.replace(".conllu", "_preprocessed.conllu")
    with open(preprocessed_file_path, "w") as outfile:
        for sentence in filtered_sentences:
            outfile.write(sentence.conll())
            outfile.write("\n\n")
    return preprocessed_file_path


def execute_evaluation(gold_file_path, predicted_file_path):
    # Read goldfile
    try:
        gold_data = load_conllu(open(gold_file_path, "r", encoding="utf-8"))
    except Exception as e:
        print(f"Skipping text because of error reading gold file {gold_file_path}: {e}")
        #raise e
        return None
    # Read predicted file and ignore some format errors
    try:
        predicted_data = load_conllu(open(predicted_file_path, "r", encoding="utf-8"), ignore_invalid_format=True)
    except Exception as e:
        print(f"Skipping text because of error reading predicted file {predicted_file_path}: {e}")
        #raise e
        return None
    # Evaluate the predictions against the gold standard
    try: #evaluate method is calling the extended version with atribute True 
        results = evaluate(gold_data, predicted_data, True) # Detailed = True, by default = False
    
    except Exception as e:
        print(f"Error during evaluation between {gold_file_path} and {predicted_file_path}: {e}")
        raise e
    return results

time_periods = ["1700-1750", "1750-1800", "1800-1850", "1850-1900", "1900-1950"]


# To look up time period index for a sample
sample_period = {"svediakorp-letter141673-Stalhammar": 0, "svediakorp-sec25-Runius": 0, "svediakorp-sec330-GyllenborgC_SwenskaSpratthoken": 0,
           "svediakorp-sec277-EnbomPU_MedborgeligtSkalde": 1, "svediakorp-sec268-DulciU_VitterhetsNojen3": 1,
           "svediakorp-sec991-spf148": 2, "svediakorp-sec252-BremerF_Teckningar1": 2, "svediakorp-sec324-GranbergPA_Enslighetsalskaren": 2,
           "svediakorp-sec254-CederborghF_BerattelseOmJohnHall": 2, "svediakorp-sec987-spf144": 2, "svediakorp-sec988-spf145": 2,
           "svediakorp-sec452-NyblomH_FantasierFyra": 3, "svediakorp-sec486-SchwartzMS_BellmansSkor": 3, "svediakorp-sec1102-spf259": 3,
           "svediakorp-sec208-Anonym_DetGrasligaMordet": 3, "svediakorp-sec1063-spf220": 3,
           "svediakorp-sec631-HasselskogN_HallaHallaGronkoping": 4, "svediakorp-sec1033-spf190": 4, "svediakorp-sec397-AngeredStrandbergH_UnderSodernsSol": 4,
           "svediakorp-sec613-EngstromA_StrindbergOchJag": 4, "svediakorp-sec639-HeidenstamV_Proletarfilosofiens": 4}

gold_dir = sys.argv[1] # validated dir
predicted_dir = sys.argv[2] # base dir

# Placeholder for samples that are skipped because of file inaccuracies
skipped_samples = []

# To look up the number of sentences for a sample
sample_nsents = defaultdict()

# Placeholder for scores of 5 time periods - 3 score types (prec, rec, f1) x number of metrics 
# Number of metrics is assigned manually so far!!! TODO: Figure out how to automize the numbers.
u_score_arrays = [np.zeros((3, 18)) for _ in range(5)]
d_score_arrays = [np.zeros((3, 38)) for _ in range(5)]

arrays = [u_score_arrays, d_score_arrays]

with open("u_scores.txt", "w") as u_outfile:
    with open("d_scores.txt", "w") as d_outfile:
        # Loop through each of the vaidated samples
        for sample in os.listdir(gold_dir):
            sample_name = sample.split("/")[-1].replace(".conllu", "")
            period = sample_period.get(sample_name) # int 0-4

            # Check that gold trees are valid
            gold_file_path = os.path.join(gold_dir, sample)
            e = check_valid_gold(gold_file_path) 
            if e: # skip invalid gold files
                for error in e:
                    print(error)
                skipped_samples.append(sample_name)
                continue
            # Check if preprocessed predicted file exists, if not create it
            try:
                predicted_file_path = os.path.join(predicted_dir, sample).replace(".conllu", "_preprocessed.conllu")
                assert os.path.exists(predicted_file_path)
            except AssertionError:
                unprocessed_predicted_file_path = os.path.join(predicted_dir, sample)
                predicted_file_path = preprocess_system_file(unprocessed_predicted_file_path, gold_file_path)
            
            # Score base tree (parser output) against validated tree (gold standard)
            results = execute_evaluation(gold_file_path, predicted_file_path)
            
           
            if not results: # skip invalid files
                skipped_samples.append(sample_name)
            # Write results to 2 different files: u_scores.txt (UPOS), d_scores.txt (DEPREL) and save to time period arrays
            else:
                # Save number of sentences in lookup dict
                sample_nsents[sample_name] = len(pyconll.load_from_file(gold_file_path))
                for i, f in enumerate([u_outfile, d_outfile]):
                    score_dict = results[i] # extraxt dict with scores for corresponding LABELS
                    f.write(f"Sample: {sample_name}, time period: {time_periods[period]}\n")
                    f.write("Metric\tPrecision\tRecall\tF1\n") 

                    metric_n = 0 # counter for loop below
                    
                    # Loop over each metric: individual UPOS and DEPREL labels
                    for metric, score in score_dict.items(): # get the metric and its 3 scores
                        if metric in results[i].keys(): # only save the relevant metrics
                            # Save scores weigthed by the number of sentences to a list of 2 arrays: 1 for UPOS, 2 for DEPREL
                            arrays[i][period][0][metric_n] += (score['precision'] * sample_nsents[sample_name])
                            arrays[i][period][1][metric_n] += (score['recall'] * sample_nsents[sample_name])
                            arrays[i][period][2][metric_n] += (score['f1'] * sample_nsents[sample_name])
                            
                        # Write to file
                        f.write(f"{metric}\t{score['precision']:.4f}\t{score['recall']:.4f}\t{score['f1']:.4f}\n")
                        metric_n += 1 # move to next metric in array
            
                f.write("\n")
        for array, (f, label_ind) in zip(arrays,[(u_outfile, 0), (d_outfile, 1)]):
            f.write(f"{'-'*70}\n")
            # After all sample scores are written, compute average scores for each time period
            for period, period_scores in enumerate(array): 
                # Get number of samples and sentences for the period
                samples_per_period = [sample_name for sample_name in sample_period.keys() 
                                    if sample_period[sample_name] == period and sample_name not in skipped_samples
                                    ]
                n_sents_per_period = sum([sample_nsents[sample_name] for sample_name in samples_per_period])
                # Write 2 output files with average scores for each time period
                f.write(
                    f"Average scores for time period {time_periods[period]}"
                    f"({len(samples_per_period)} samples with a total of {n_sents_per_period} sentences):\n")
                f.write("Metric\tPrecision\tRecall\tF1\n")
                for n, metric in enumerate(results[label_ind].keys()):
                    # Normalize weigthed averages by the total number of sentences for the time period
                    precision_avg = period_scores[0][n] / n_sents_per_period
                    recall_avg = period_scores[1][n] / n_sents_per_period
                    f1_avg = period_scores[2][n] / n_sents_per_period
                
                    f.write(
                        f"{metric}\t{precision_avg:.4f}\t{recall_avg:.4f}\t{f1_avg:.4f}\n")
                f.write("\n")
