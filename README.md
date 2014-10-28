ak-oca-clabot
=============

Sends a comment on GitHub Pull Request if
there are some authors of commits that have not signed the OCA CLA.

Requirements:
 - Python 3
 - requests
 - erppeek

Quickstart:
 - set configuration parameters in clabot.ini file
 - python3 clabot.py clabot.ini


Start Tutorial:
===============

In clabot.ini:
--------------

 Follow these little steps to set up your CLA bot :
 + Set login and password of your bot's GitHub account
 + Set the different repositories' tokens you want to follow
 + Set Odoo's URL : e.g http://your-odoo.com
 + Set login, password of the bot's Odoo account
 + Set Odoo's database to use
 + Set the name of the category_id (in res.partner) that you want to check in Odoo's database : e.g cla
 + Set the GitHub login field's name in your Odoo's database (must be in res.partner)

 NB : You can edit the sent message as you want. Just keep the two variables {user} and {users} that correspond respectively to the PR's author and to the list of users that have not signed the CLA.
