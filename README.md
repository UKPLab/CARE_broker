# CARE Broker

This repository contains the broker for [CARE](https://github.com/UKPLab/CARE), but could also be used standalone.
The broker allows running multiple models in parallel and to distribute it via websockets.
We currently support several skills out of the box:

- [OpenAI Azure API](https://learn.microsoft.com/en-us/azure/ai-services/openai)
- [Huggingface Pipeline](https://huggingface.co/docs/transformers/pipeline_tutorial)
- [Llama.cpp](https://github.com/ggerganov/llama.cpp) through [Python bindings](https://llama-cpp-python.readthedocs.io/en/latest/)
- [NLTK Vader Sentiment Analysis](https://www.nltk.org/_modules/nltk/sentiment/vader.html)

## Requirements

* [Docker](https://docs.docker.com/get-docker/)
* [GNU Make](https://www.gnu.org/software/make/)

__Note:__ On Windows, you need to install [GnuWin32 Make](http://gnuwin32.sourceforge.net/packages/make.htm) or just run `winget install GnuWin32.Make` and make it executable with `set PATH=%PATH%;C:/Program Files (x86)/GnuWin32/bin`.

## Documentation

We provide a complete documentation of the broker. It can be built locally or found [here](https://care.ukp.informatik.tu-darmstadt.de/doc_nlp_broker/index.html) of a prebuilt version.

```shell
make doc
```

After the documentation has been built, it can be found under `docs/build/html/index.html`.
There is also a description of the asynchronous communication protocol that is used by the broker under `docs/html/index.html`.

## Contact 

_Maintainers:_

* Dennis Zyska (dennis.zyska@tu-darmstadt.de) 
* Nils Dycke (nils.dycke@tu-darmstadt.de)

Don't hesitate to send us an e-mail or report an issue, if something is broken (and it shouldn't be) or if you have further questions.

https://www.ukp.tu-darmstadt.de \
https://www.tu-darmstadt.de

### Citation

If you use this software, please cite the following paper:

```bibtex
@inproceedings{zyska-etal-2023-care,
    title = "{CARE}: Collaborative {AI}-Assisted Reading Environment",
    author = "Zyska, Dennis  and
      Dycke, Nils  and
      Buchmann, Jan  and
      Kuznetsov, Ilia  and
      Gurevych, Iryna",
    booktitle = "Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 3: System Demonstrations)",
    month = jul,
    year = "2023",
    address = "Toronto, Canada",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2023.acl-demo.28",
    doi = "10.18653/v1/2023.acl-demo.28",
    pages = "291--303",
    abstract = "Recent years have seen impressive progress in AI-assisted writing, yet the developments in AI-assisted reading are lacking. We propose inline commentary as a natural vehicle for AI-based reading assistance, and present CARE: the first open integrated platform for the study of inline commentary and reading. CARE facilitates data collection for inline commentaries in a commonplace collaborative reading environment, and provides a framework for enhancing reading with NLP-based assistance, such as text classification, generation or question answering. The extensible behavioral logging allows unique insights into the reading and commenting behavior, and flexible configuration makes the platform easy to deploy in new scenarios. To evaluate CARE in action, we apply the platform in a user study dedicated to scholarly peer review. CARE facilitates the data collection and study of inline commentary in NLP, extrinsic evaluation of NLP assistance, and application prototyping. We invite the community to explore and build upon the open source implementation of CARE.Github Repository: \url{https://github.com/UKPLab/CAREPublic} Live Demo: \url{https://care.ukp.informatik.tu-darmstadt.de}",
}
```

### Disclaimer

This repository contains experimental software and is published for the sole purpose of giving additional background details on the respective publication.\
The software is only tested on unix systems and is not guaranteed to work on other operating systems.
