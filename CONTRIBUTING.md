# Contributing

Thanks for considering making an addition to this project! These contributing guidelines should help make your life easier. 

Before starting, some things to consider:
* For larger features, it would be helpful to get in touch first (through issue/email)
* A lot of the logic is in `docdeid`, please consider making a PR there for things that are not specific to `deduce`.
* `deduce` is a rule-based de-identifier
* In case you would like to see any rules added/removed/changed, a decent substantiation (with examples) of the potential improvement is useful

## Setting up the environment

* This project uses poetry for package management. Install it with ```pip install poetry```
* Set up the environment is easy, just use ```poetry install```
* The makefile contains some useful commands when developing:
  * `make test` runs the tests (including coverage)
  * `make format` formats the package code
  * `make lint` runs the linters (check the output)
  * `make clean` removes build/test artifacts, etc
* And for docs:
  * `make build-docs` builds the docs
  * `make clean-docs` removes docs build

## PR checlist

* Verify that tests are passing
* Verify that tests are updated/added according to changes
* Run the formatters (`make format`)
* Run the linters (`make lint`) and check the output for anything preventable
* Add a section to the changelog
* Add a description to your PR

## Releasing
* Readthedocs has a webhook connected to pushes on the main branch. It will trigger and update automatically. 
* Create a [release on github](https://github.com/vmenger/docdeid/releases/new), create a tag with the right version, manually copy and paste from the changelog
* Build pipeline and release to PyPi trigger automatically on release

Any other questions/issues not covered here? Please just get in touch!