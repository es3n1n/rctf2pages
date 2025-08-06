# rctf2pages

Links rot, which would be especially sad when you have a beautifully themed
rCTF website :(. None of the existing rCTF archival technologies archive the
entire website and keep it browsable; in most cases, they only archive the
handouts and the challenge descriptions.

This is why we created rctf2pages. Github Pages can now host a static version
of a rCTF site long after the CTF event is over.

Challenges that need special hosting requirements, such as netcat-based
challenges, are not in scope of this project, unfortunately. Though I guess
you can try to figure the challenges out from the given handouts (if any) or
public releases of challenge source code repositories (if available).

### Examples

A ~~picture~~ live site is worth a thousand words:

- Malta CTF [Quals 2025](https://quals.2025.ctf.mt/)
- idekCTF [2025](https://2025.idek.team/)
- (Feel free to send us a PR and add yours here)

## Usage

It's mostly just bash, JavaScript and Python. To install dependencies:

```bash
$ npm install
$ python3 -m pip install -r requirements.txt
```

This tool is separated into many stages, each does a different operation.
To see usage information:

```bash
$ ./stage
Usage: ./stage [stage number]
Stages:

  ./stage 00            init
  ./stage 01            scrape
  ./stage 02            json_resolve
[...]
```

Each stage will operate on the git repository, but will not push unless
otherwise specified. To see what each stage does check `run.sh` for the
commit title, and `stage.sh` for the executed commands.

After all stages (but before pushing), you'd have to patch out a few things manually:

- Change landing page image urls in html config, if you've used direct urls (they would be downloaded too).
- Everything else should be ✨automatically✨ handled by the 05 and 06 stages.

### Development Environment

After you've finished preparing your archived CTF for publication, it never hurts to check how it will actually be displayed to people once you deploy it on GitHub Pages.

To do that, you can use the [`serve.py`](serve.py) Python script, which somewhat emulates the behavior of a GitHub Pages web server. To use it, just invoke it from the CTF directory, and your site will be available at `localhost:8000`.

### GitHub Pages Setup

Follow [GitHub documentation](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site).
In particular, you need to setup a `CNAME` DNS record on your DNS provider to
`<user>.github.io` or `<organization>.github.io`. You also need to set the
"Custom domain" setting under GitHub Pages settings for the repository.

## License

Copyright 2025 es3n1n \
Copyright 2022 SIGPwny \
Copyright 2022 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

&emsp; http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
