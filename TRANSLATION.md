# Translation Contribution

To translate in any language, the language specific `django.po` file is present at `apps/locale/<language-code>/LC_MESSAGES/django.po`.
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

If `msgid`(s) in the `django.po` file of a language that you want to translate to are not present, then you can simply copy the contents of another language's `django.po` file, and paste it into yours, and translate the `msgstr`(s) for each `msgid` in your language.
