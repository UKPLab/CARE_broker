# CARE Broker

This repository contains the broker for [CARE](https://github.com/UKPLab/CARE).
The broker allows running multiple models in parallel and to distribute it to CARE.
A model example for inference can be found [here](https://github.com/UKPLab/CARE_models).

## Requirements

* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)

## Documentation

We provide a complete documentation of the broker that can be built locally.

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


### Disclaimer

This repository contains experimental software and is published for the sole purpose of giving additional background details on the respective publication.\
The software is only tested on unix systems and is not guaranteed to work on other operating systems.
