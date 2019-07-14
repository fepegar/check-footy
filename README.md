Script I use to check every 5 minutes and send a push notification to my phone
if there's a new football game available at King's College London.

## Install requirements

```shell
$ conda create -n "footy" python
$ conda activate "footy"
$ pip install -r "requirements.txt"
```

## Usage
Add this job to `crontab`:

```shell
*/5 * * * * export SIMPLEPUSH="HuxgBB" && $HOME/miniconda3/envs/footy/bin/python $HOME/git/check-footy/check_footy.py
```

Where `HuxgBB` should be replaced by your [Simplepush](https://simplepush.io/) key (Simplepush has a free trial period of 7 days).
