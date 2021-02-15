# VacTrend

![build-site](https://github.com/lambdapioneer/vactrend/workflows/build-site/badge.svg)

This is a personal project for experimenting with GitHub Actions. As a side-effect, it creates a regularly updating website that shows historic data of COVID vaccinations in the UK and Germany along with some trend extrapolation.

Website: https://lambdapioneer.github.io/vactrend/

To run locally:

```
$ python -mvenv env
$ source env/bin/activate
(env)$ python -mpip install -r requirements.txt
(env)$ python main.py
(env)$ firefox public/index.html
```

Screenshot:

<a href="screenshot.png"><img src="screenshot.png" width="640px" /></a>