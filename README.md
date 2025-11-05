# Diachronic_Treebanks_DigPhil
Diachronic dataset for the project's experiments. Part of the group research project Diachronic Treebanks of DigPhil.

## Dataset Description

The data is compiled from Swedish Diachnoric Corpus:

Eva Pettersson and Lars Borin (2022)
Swedish Diachronic Corpus
In Darja Fišer & Andreas Witt (eds.), CLARIN. The Infrastructure for Languag\ e Resources. Berlin: deGruyter. https://degruyter.com/document\ /doi/10.1515/9783110767377-022/html


The dataset consists of literary texts from different periods of Modern Swedish. The texts are grouped into 50-year intervals. In the later periods, the collections primarily contain prose fiction, while the earlier periods also include private correspondence and drama, reflecting the relative scarcity of prose literature from those times.

| Period    | Number of Sentences |
|-----------|----------------------|
| 1700–1749 | 7,305               |
| 1750–1799 | 18,855              |
| 1800–1849 | 10,305              |
| 1850–1899 | 10,160              |
| 1900–1950 | 11,768              |

The data was parsed using Stanza (reference) and a small amount of Stanza's output has been corrected by human experts (participants in the group project). The "parsed_data/validated" directory contains consensus forms by two or more annotators.

## Scoring

# Inter-annotator agreement
Add text here

# Parser output
With the validated gold standard UD trees, we are able to score automatic parsing results. Presented below are the scores for Stanza, normalized by the number of sentences for each time period.

1700-1750 (3 samples with a total of 15 sentences):
Metric	Precision	Recall	F1	Aligned Accuracy
UPOS	0.7713	0.7782	0.7747	0.7854
UAS	0.5813	0.5869	0.5841	0.5927
LAS	0.4882	0.4933	0.4907	0.4985

1750-1800 (2 samples with a total of 17 sentences):
Metric	Precision	Recall	F1	Aligned Accuracy
UPOS	0.6568	0.6568	0.6568	0.9323
UAS	0.5182	0.5182	0.5182	0.7586
LAS	0.4767	0.4767	0.4767	0.7030

1800-1850 (6 samples with a total of 28 sentences):
Metric	Precision	Recall	F1	Aligned Accuracy
UPOS	0.9360	0.9348	0.9354	0.9515
UAS	0.7752	0.7741	0.7746	0.7870
LAS	0.7275	0.7266	0.7270	0.7391

1850-1900 (5 samples with a total of 24 sentences):
Metric	Precision	Recall	F1	Aligned Accuracy
UPOS	0.9704	0.9704	0.9704	0.9704
UAS	0.8008	0.8008	0.8008	0.8008
LAS	0.7545	0.7545	0.7545	0.7545

1900-1950 (5 samples with a total of 25 sentences):
Metric	Precision	Recall	F1	Aligned Accuracy
UPOS	0.9736	0.9736	0.9736	0.9736
UAS	0.8552	0.8552	0.8552	0.8552
LAS	0.8148	0.8148	0.8148	0.8148

