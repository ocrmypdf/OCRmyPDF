---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
What command line or API call were you trying to run?

```bash
ocrmypdf  ...arguments... input.pdf output.pdf
```

Run with verbosity or higher `-v1` to see more detailed logging. This information may be helpful.

**Example file**
Include an input PDF or image that demonstrates your issue.

Please provide an input file with no personal or confidential information. At your option you may `GPG-encrypt the file <https://github.com/jbarlow83/OCRmyPDF/wiki>` for OCRmyPDF's author only.

Links to files hosted elsewhere are perfectly acceptable. You could also look in ``tests/resources`` and see if any of those files reproduce your issue.

(Exceptions: Issues with installation, command line argument parsing, test suite failures.Issues without example files usually cannot be resolved.)

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**System**
 - OS: [e.g. Linux, Windows, macOS]
 - OCRmyPDF Version: ``ocrmypdf --version``
 - How did you install ocrmypdf? Did you use a system package manager, `pip`, or a Docker image?
