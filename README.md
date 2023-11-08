# Extracting a PP Attachment Disambiguation Dataset for German

This repository contains code for extracting
a PP attachment disambiguation dataset from the paper
[Parsers Know Best: German PP Attachment Revisited](https://aclanthology.org/2020.coling-main.185/)
published at COLING 2020.

## Usage

### Requirements
* Python 3

### CLI
Run:
```shell
python pp_extract_candidate.py --help
```
to see the usage.

Run the sample data:
```shell
python pp_extract_candidate.py data/input.conll data/output.txt
```

### Input

The input is a file in CoNLL format:
* Column 1: ID
* Column 2: word form
* Column 4: gold POS tag
* Column 5: predicted POS tag
* Column 7: gold dependency head
* Column 8: gold dependency label
* Column 9: predicted dependency head
* Column 10: predicted dependency label
* Column 11: topological field (TF) tag

### Output

Each line contains several fields separated by a space:
* ID
* The preposition, its POS and TF tags
* The preposition object, its POS and TF tags
* List of candidates, each contains:
  * The candidate head, its POS and TF tags
  * The absolute and relative distances between the candidate head and the
    preposition
  * A label indicating it is the true head (1) or not (0)


### Examples
* If the data only contain the gold dependency head and label (i.e., columns 9 and 10 are `_`),
  use `--only_gold`.
* For the train and dev sets, use in addition `--add_gold_head`.

## Citation

```bib
@inproceedings{do-rehbein-2020-parsers,
    title = "Parsers Know Best: {G}erman {PP} Attachment Revisited",
    author = "Do, Bich-Ngoc and Rehbein, Ines",
    editor = "Scott, Donia and Bel, Nuria and Zong, Chengqing",
    booktitle = "Proceedings of the 28th International Conference on Computational Linguistics",
    month = dec,
    year = "2020",
    address = "Barcelona, Spain (Online)",
    publisher = "International Committee on Computational Linguistics",
    url = "https://aclanthology.org/2020.coling-main.185",
    doi = "10.18653/v1/2020.coling-main.185",
    pages = "2049--2061",
}
```