# Translation Contribution

To translate in any language, the language specific `django.po` file is present at `locale/<language-code>/LC_MESSAGES/django.po`.
The `<language-code>` is the code for specific language. (like `hi` for Hindi)

The format of translation is

```po
msgid "Message ID"
msgstr "Message value"
msgid "Some Message ID"
msgstr "Some Message value"
```

Following is an example for `hi` language code

```po

msgid "You're welcome"
msgstr "आपका स्वागत है"
msgid "Bye"
msgstr "अलविदा"
```

If `msgid`(s) in the `django.po` file of a language that you want to translate to are not present, then you can add them by following the below steps.

Add missing `msgid`s in `.po` files by enclosing text in `{% trans %}` or `{% blocktrans %}` in html templates, then run the following

```bash
py manage.py makemessages --ignore=*.txt
```

To compile `.po` files to `.mo` files for translation availablity

```bash
py manage.py compilemessages
```
