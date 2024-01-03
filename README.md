# SendMails
A flexible python package to send mails with attachments from your server.
It supports mailx, mutt mail clients.
Text attachments are split depending on the size limit (Should be lower than your Transfer protocol size limit).
Non-textual attachments are compressed and attached.
Prerequisites:
- Required python packages installed.
- Supported mail client installed.