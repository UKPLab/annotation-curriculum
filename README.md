# Annotation Curricula to Implicitly Train Non-Expert Annotators
### Ji-Ung Lee`*`, Jan-Christoph Klie`*`, and Iryna Gurevych
#### [UKP Lab, TU Darmstadt](https://www.informatik.tu-darmstadt.de/ukp/ukp_home/index.en.jsp)
`*` Both authors contributed equally.

Source code and user models from our experiments of our [CL 2021 submission](). 

> **Abstract:** Annotation studies often require annotators to familiarize themselves with the task, its annotation scheme, and the data domain. This can be overwhelming in the beginning, mentally taxing, and induce errors into the resulting annotations; especially in citizen science or crowd sourcing scenarios where domain expertise is not required and only annotation guidelines are provided. To alleviate these issues, we propose annotation curricula, a novel approach to implicitly train annotators. We gradually introduce annotators into the task by ordering instances that are annotated according to a learning curriculum. To do so, we first formalize annotation curricula for sentence- and paragraph-level annotation tasks, define an ordering strategy, and identify well-performing heuristics and interactively trained models on three existing English datasets. We then conduct a user study with 40 voluntary participants who are asked to identify the most fitting misconception for English tweets about the Covid-19 pandemic. Our results show that using a simple heuristic to order instances can already significantly reduce the total annotation time while preserving a high annotation quality. Annotation curricula thus can provide a novel way to improve data collection. To facilitate future research, we further share our code and data consisting of 2,400 annotations.

* **Contact** 
    * Jan-Christoph Klie (klie@ukp.informatik.tu-darmstadt.de) 
    * Ji-Ung Lee (lee@ukp.informatik.tu-darmstadt.de) 
    * UKP Lab: http://www.ukp.tu-darmstadt.de/
    * TU Darmstadt: http://www.tu-darmstadt.de/

Drop us a line or report an issue if something is broken (and shouldn't be) or if you have any questions.

For license information, please see the LICENSE and README files.

> This repository contains experimental software and is published for the sole purpose of giving additional background details on the respective publication. 

## Project structure

* `active_learning` &mdash; Our active learning strategies
* `data` &mdash; Folder to put the data
* `learner_models` &mdash; Our simulated learner models
* `models` &mdash; Folder for storing our trained deep learning models
* `readers` &mdash; Datareader
* `results` &mdash; Result folder
* `user_simulation` &mdash; Code the handing simulated learner models 

## Setting up the experiments

```python
pip install -r requirements.txt
```
## Running the experiments

```python
python train_model.py
```
### Parameters
The code offers a range of parameters which can be set:

`--train` &mdash; Path to the (initially unlabeled) training data.

`--test` &mdash; Path to the test data.

`--seed` &mdash; Random seed to use.

`--epochs` &mdash; Number of epochs.


## Data
The collected data from our study is provided on tu-datalib under a CC-by 4.0 license. 

To reproduce our experiments, please collect the 


## Citing the paper

Please cite our paper as:
```
@inproceedings{lee-etal-2021-annotation-curriculum,
    title = "{A}nnotation {C}urricula to {I}mplicitly {T}rain {N}on-{E}xpert {A}nnotators",
    author = "Lee, Ji-Ung  and
      Klie, Jan-Christoph  and
      Gurevych, Iryna",    
    month = jun,
    year = "2021",
    journal = "arxiv-preprint.",   
}
```
