# Translation Contribution

If `msgid`(s) in the `django.po` file of a language that you want to translate to are not present, then you can add them by following the below steps.

Add missing `msgid`s in `.po` files by enclosing text in `{% trans %}` or `{% blocktrans %}` in html templates, then run the following

```bash
py manage.py makemessages --extension=html,js
```

After that, you may create translations for now available msgids for your respective language in the format mentioned above.

Then, compile `.po` files to `.mo` files to load translations, run the following

```bash
py manage.py compilemessages
```
