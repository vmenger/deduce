## Contribution to DEDUCE

First of all, thanks a lot for considering to contribute to our open source project. DEDUCE is largely maintainted by volunteers aiming to facilitate awesome clinical NLP research and applications, and we are are happy you want to join us doing that.  

### Opening an issue

The first step to get help or file a bug report is [opening an issue](https://github.com/vmenger/deduce/issues). Before you open an issue, please take a few moments to check that your issue has not already been answered before. We don't have a template for opening an issue – please just try to be specific and complete in your information, so your issue can be tackled. 

Please note that this project is maintained mostly by volunteers, and an immediate resonse is not always possible. However, if no reply happens in 1-2 weeks or so, feel free to ping a reminder by tagging one of the maintainers. 

### Making a contribution 

Contributes to docs/code are very much welcomed. If you roughly adhere to the following steps, the chances of your work ending up in the repository are greatly increased. 

* If you are planning to do considerable work, please get in touch by opening an issue first, outlining the changes you are planning. 
* Create a new branch based on the `next-release` branch, but please check it is up to date with master.
* Setup your environment. You most likely need `pip install -r requirements.txt requirements-dev.txt`
* Commit your work to this branch. In general, try to roughly adhere to the dominant coding/documentation style of the repository. 
* After your work is finished, please run locally:
  * `make test` – to run the tests. If a test fails, it is likely something is wrong in your code. However, sometimes the test is wrong. If you make any changes to the test, please make a comment in the PR. 
  * `make format` – this will format all files into the [Black formatting style](https://github.com/psf/black), and output a log of `pylint`. Please check the `pylint` output if you have introduced any preventable errors. We do not strive for perfection, but we appreciate well-linted code. 
* You are now ready to [open a PR](https://github.com/vmenger/deduce/pulls) from your branch to `next-release`. In your message, briefly describe the work you did, and anything important to know for reviewing. 
* One of the maintainers will automatically be notified and review your work. Again, we are largely doing this in our own time, so we cannot always immediately process a PR, but feel free to ping a reminder by tagging one of the maintainers if nothing happens in 1-2 weeks. 
* Hopefully, we can now merge your work into the repository, possibly after some rounds of feedback/review. We aim to release improvements that deliver value to DEDUCE immediately to `master` and `pypi`. 

In any case, your help is greatly appreciated, and these guidelines are intended to be a help rather than an obstacle to your contribution. If you get stuck anywhere, opening an issue is always possible!